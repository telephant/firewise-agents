"""
Router Agent for Financial Data Entry

Two-stage LangGraph agent:
1. Router: Classify user intent → sub_type + action
2. Task Executor: Execute specific task with focused prompt

See docs/ROUTER_AGENT_DESIGN.md for full documentation.
"""

import json
import logging
from typing import List, Dict, Any, TypedDict, Optional, Annotated
import operator

from langchain.globals import set_debug
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph, END

from config import settings
from schemas.chat_schema import ChatRequest, ChatResponse, ExecutedAction, RouterResult, PreviewData
from tools import set_api_client, clear_api_client, CHAT_TOOLS
from prompts.chat_prompts import ROUTER_PROMPT, get_task_prompt
from stores import conversation_store

# Enable LangChain debug mode
set_debug(True)

logger = logging.getLogger(__name__)

# Maximum tool call iterations
MAX_ITERATIONS = 5


# =============================================================================
# LANGGRAPH STATE
# =============================================================================

class AgentState(TypedDict):
    """State for LangGraph agent flow."""
    # Input
    message: str
    user_id: str
    conversation_id: Optional[str]
    auth_token: str
    api_base_url: str

    # Router output
    sub_type: Optional[str]
    action: Optional[str]
    confidence: float

    # Prefetch output
    default_cash_id: Optional[str]
    default_cash_name: Optional[str]

    # Task state
    messages: Annotated[List[BaseMessage], operator.add]
    executed_actions: List[ExecutedAction]
    task_completed: bool
    iteration: int

    # Preview mode (Main Stage Hijack)
    preview_action: Optional[str]
    preview_data: Optional[PreviewData]

    # Output
    response: Optional[str]
    error: Optional[str]


# =============================================================================
# ROUTER NODE
# =============================================================================

async def router_node(state: AgentState) -> Dict[str, Any]:
    """
    Classify user intent and determine sub_type + action.
    Uses a lightweight LLM call without tools.
    Skips classification if sub_type already exists (follow-up message).
    """
    # Skip router if this is a follow-up message with existing context
    if state.get("sub_type") and state.get("confidence", 0) > 0:
        logger.info(f"Router: skipping (follow-up), using existing: {state['sub_type']}/{state.get('action')}")
        return {
            "sub_type": state["sub_type"],
            "action": state.get("action"),
            "confidence": state.get("confidence", 1.0),
        }

    logger.info(f"Router: classifying message: {state['message'][:50]}...")

    llm = ChatOpenAI(
        model=settings.model_name,
        openai_api_base=settings.openai_api_base,
        openai_api_key=settings.openai_api_key,
        temperature=0,
    )

    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=state["message"]),
    ])

    # Parse JSON response
    try:
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)

        sub_type = result.get("sub_type", "unknown")
        action = result.get("action")
        confidence = result.get("confidence", 0.0)

        logger.info(f"Router result: sub_type={sub_type}, action={action}, confidence={confidence}")

        return {
            "sub_type": sub_type,
            "action": action,
            "confidence": confidence,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Router JSON parse error: {e}, content: {response.content}")
        return {
            "sub_type": "unknown",
            "action": None,
            "confidence": 0.0,
            "error": "Failed to classify request",
        }


# =============================================================================
# CLARIFY NODE
# =============================================================================

async def clarify_node(state: AgentState) -> Dict[str, Any]:
    """
    Ask user to clarify when router can't classify.
    """
    clarify_message = get_task_prompt("unknown")

    return {
        "response": clarify_message,
        "task_completed": False,
    }


# =============================================================================
# TASK EXECUTOR NODE
# =============================================================================

async def task_executor_node(state: AgentState) -> Dict[str, Any]:
    """
    Execute the classified task with specific prompt and tools.
    Runs tool execution loop.
    """
    sub_type = state["sub_type"]
    action = state["action"]
    default_cash_id = state.get("default_cash_id")
    default_cash_name = state.get("default_cash_name")

    logger.info(f"Task executor: sub_type={sub_type}, action={action}")
    if default_cash_id:
        logger.info(f"Using prefetched cash account: {default_cash_name} ({default_cash_id})")

    # Set up API client
    set_api_client(state["api_base_url"], state["auth_token"])

    try:
        # Get task-specific prompt
        task_prompt = get_task_prompt(sub_type, action)

        # Create LLM with tools
        llm = ChatOpenAI(
            model=settings.model_name,
            openai_api_base=settings.openai_api_base,
            openai_api_key=settings.openai_api_key,
            temperature=0.3,
        )
        llm_with_tools = llm.bind_tools(CHAT_TOOLS)

        # Get conversation for history
        conversation = conversation_store.get_or_create(
            state["conversation_id"],
            state["user_id"]
        )

        # Check if different intent from previous conversation
        if conversation.messages:
            prev_sub_type = getattr(conversation, 'sub_type', None)
            if prev_sub_type and prev_sub_type != sub_type:
                # Different intent, clear history
                conversation.messages.clear()
                logger.info(f"Different intent ({prev_sub_type} -> {sub_type}), cleared history")

        # Store current sub_type in conversation
        conversation.sub_type = sub_type
        conversation.action = action

        # Build messages
        messages: List[BaseMessage] = [
            SystemMessage(content=task_prompt),
            *build_messages_from_history(conversation.get_history()),
            HumanMessage(content=state["message"]),
        ]

        # Add current message to history
        conversation.add_message("user", state["message"])

        executed_actions: List[ExecutedAction] = []
        task_completed = False

        # Tool execution loop
        for iteration in range(MAX_ITERATIONS):
            logger.info(f"Task iteration {iteration + 1}")

            response = await llm_with_tools.ainvoke(messages)

            # No tool calls - return response
            if not response.tool_calls:
                assistant_message = response.content or "I'm not sure how to help with that."
                conversation.add_message("assistant", assistant_message)

                # Clear conversation if task completed
                if task_completed:
                    conversation_store.delete(conversation.id)
                    logger.info(f"Task completed, cleared conversation: {conversation.id}")

                return {
                    "response": assistant_message,
                    "executed_actions": executed_actions,
                    "task_completed": task_completed,
                }

            # Process tool calls
            messages.append(response)

            # Transaction tools that trigger preview mode (Main Stage Hijack)
            TRANSACTION_TOOLS = (
                "asset_transaction",
                "debt_transaction",
                "record_income",
                "record_expense",
            )

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"Tool call: {tool_name}")
                logger.debug(f"Tool args: {tool_args}")

                # Check if this is a transaction tool - return preview instead of executing
                if tool_name in TRANSACTION_TOOLS:
                    # Auto-fill defaults before building preview
                    tool_args = auto_fill_defaults(tool_name, tool_args, state)

                    # Build preview data from tool args
                    preview_data = build_preview_data(tool_name, tool_args, sub_type, action)

                    if preview_data:
                        logger.info(f"Returning preview for {tool_name}: {preview_data}")

                        # Clear conversation since we're ready for preview
                        conversation_store.delete(conversation.id)

                        return {
                            "response": "I've prepared this for you. Please review the details:",
                            "preview_action": "preview",
                            "preview_data": preview_data,
                            "executed_actions": [],
                            "task_completed": False,  # Will complete after user confirms
                        }

                # Execute non-transaction tools normally
                result = await execute_tool(tool_name, tool_args, state)
                success = result.get("success", False)

                messages.append(
                    ToolMessage(
                        content=json.dumps(result),
                        tool_call_id=tool_call["id"],
                    )
                )

        # Max iterations
        return {
            "response": "I'm having trouble completing this request. Please try again.",
            "executed_actions": executed_actions,
            "task_completed": False,
            "error": "Max iterations reached",
        }

    finally:
        clear_api_client()


# =============================================================================
# PRE-FETCH NODE - Get default cash account if needed
# =============================================================================

# Sub-types that need default cash account
# For record_income: to_asset_id = cash
NEEDS_CASH_TO = {"salary", "bonus", "dividend", "interest", "freelance", "gift", "rental", "capital_gains", "refund"}
# For record_expense and debt_transaction(pay): from_asset_id = cash
NEEDS_CASH_FROM = {"expense", "mortgage_payment", "personal_loan_payment", "credit_card_payment", "student_loan_payment", "auto_loan_payment"}
# For asset_transaction(invest): from_asset_id = cash
NEEDS_CASH_BUY = {"stock_buy", "etf_buy", "crypto_buy", "bond_buy", "real_estate_add"}
# For asset_transaction(sell): to_asset_id = cash
NEEDS_CASH_SELL = {"stock_sell", "etf_sell", "crypto_sell", "bond_sell"}
# Note: cash_add and deposit_add don't need cash prefetch - they create the cash account itself


def _needs_fill(value) -> bool:
    """Check if a value needs to be auto-filled (empty, None, or placeholder)."""
    if not value:
        return True
    if isinstance(value, str) and value.upper() in ("DEFAULT", "CASH", "AUTO"):
        return True
    return False


def auto_fill_defaults(tool_name: str, args: dict, state: AgentState) -> dict:
    """Auto-fill default values based on tool and sub_type."""
    cash_id = state.get("default_cash_id")
    if not cash_id:
        return args

    sub_type = state.get("sub_type", "")
    action = state.get("action")
    key = f"{sub_type}_{action}" if action else sub_type

    # record_income: to_asset_id = cash
    if tool_name == "record_income":
        if sub_type in NEEDS_CASH_TO and _needs_fill(args.get("to_asset_id")):
            args["to_asset_id"] = cash_id
            logger.info(f"Auto-filled to_asset_id={cash_id} for income")

    # record_expense: from_asset_id = cash
    elif tool_name == "record_expense":
        if _needs_fill(args.get("from_asset_id")):
            args["from_asset_id"] = cash_id
            logger.info(f"Auto-filled from_asset_id={cash_id} for expense")

    # asset_transaction
    elif tool_name == "asset_transaction":
        tx_type = args.get("transaction_type")
        # invest: from_asset_id = cash (you spend cash to buy)
        if tx_type == "invest" and _needs_fill(args.get("from_asset_id")):
            args["from_asset_id"] = cash_id
            logger.info(f"Auto-filled from_asset_id={cash_id} for invest")
        # sell: to_asset_id = cash (you receive cash from selling)
        if tx_type == "sell" and _needs_fill(args.get("to_asset_id")):
            args["to_asset_id"] = cash_id
            logger.info(f"Auto-filled to_asset_id={cash_id} for sell")

    # debt_transaction: from_asset_id = cash for payments
    elif tool_name == "debt_transaction":
        tx_type = args.get("transaction_type")
        if tx_type == "pay" and _needs_fill(args.get("from_asset_id")):
            args["from_asset_id"] = cash_id
            logger.info(f"Auto-filled from_asset_id={cash_id} for debt payment")

    return args


async def prefetch_node(state: AgentState) -> Dict[str, Any]:
    """
    Pre-fetch default cash account via direct API call (not LLM).
    Calls GET /fire/assets/default-cash endpoint.
    """
    sub_type = state.get("sub_type")
    action = state.get("action")

    # Build key for checking
    key = f"{sub_type}_{action}" if action else sub_type

    # Check if we need to pre-fetch cash account
    needs_cash = (
        sub_type in NEEDS_CASH_TO or
        sub_type in NEEDS_CASH_FROM or
        key in NEEDS_CASH_BUY or
        key in NEEDS_CASH_SELL
    )

    if not needs_cash:
        return {}

    # Direct API call to dedicated endpoint
    from tools.api_client import APIClient

    try:
        client = APIClient(state["api_base_url"], state["auth_token"])
        result = await client.get("/fire/assets/default-cash")

        if result.get("success") and result.get("data"):
            cash = result["data"]
            logger.info(f"Pre-fetched cash account: {cash['name']} ({cash['id']})")
            return {
                "default_cash_id": cash["id"],
                "default_cash_name": cash["name"],
            }

        logger.warning("No cash account found for user")
        return {}

    except Exception as e:
        logger.error(f"Prefetch API error: {e}")
        return {}


# =============================================================================
# CONDITIONAL EDGES
# =============================================================================

def should_clarify(state: AgentState) -> str:
    """Determine if we need to clarify or can execute."""
    if state.get("sub_type") == "unknown" or state.get("confidence", 0) < 0.5:
        return "clarify"
    return "prefetch"


# =============================================================================
# BUILD GRAPH
# =============================================================================

def build_agent_graph() -> StateGraph:
    """Build the LangGraph agent."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("prefetch", prefetch_node)
    workflow.add_node("task_executor", task_executor_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        should_clarify,
        {
            "clarify": "clarify",
            "prefetch": "prefetch",
        }
    )

    # Prefetch -> task_executor
    workflow.add_edge("prefetch", "task_executor")

    # Terminal edges
    workflow.add_edge("clarify", END)
    workflow.add_edge("task_executor", END)

    return workflow.compile()


# Compiled graph
agent_graph = build_agent_graph()


# =============================================================================
# HELPERS
# =============================================================================

def build_preview_data(
    tool_name: str,
    tool_args: dict,
    sub_type: Optional[str],
    action: Optional[str]
) -> Optional[PreviewData]:
    """
    Build preview data from tool arguments for Main Stage Hijack.

    Maps tool args to the PreviewData schema that the frontend expects.
    """
    try:
        # Map tool name + sub_type to category
        category = _get_category(tool_name, sub_type, action, tool_args)

        preview = PreviewData(
            category=category,
            amount=tool_args.get("amount"),
            currency=tool_args.get("currency"),
            to_asset_id=tool_args.get("to_asset_id"),
            from_asset_id=tool_args.get("from_asset_id"),
            debt_id=tool_args.get("debt_id"),
            description=tool_args.get("description"),
            shares=tool_args.get("shares"),
            ticker=tool_args.get("ticker"),
            date=tool_args.get("date"),
        )

        return preview

    except Exception as e:
        logger.error(f"Error building preview data: {e}")
        return None


def _get_category(
    tool_name: str,
    sub_type: Optional[str],
    action: Optional[str],
    tool_args: dict
) -> str:
    """Map tool name and sub_type to flow category for preview."""

    # record_income: use sub_type directly (salary, bonus, dividend, etc.)
    if tool_name == "record_income":
        return sub_type or "salary"

    # record_expense
    if tool_name == "record_expense":
        return "expense"

    # asset_transaction: map transaction_type
    if tool_name == "asset_transaction":
        tx_type = tool_args.get("transaction_type", "invest")
        if tx_type == "invest":
            return "invest"
        elif tx_type == "sell":
            return "sell"
        elif tx_type == "dividend":
            return "dividend"
        elif tx_type == "interest":
            return "interest"
        return "invest"

    # debt_transaction
    if tool_name == "debt_transaction":
        tx_type = tool_args.get("transaction_type", "pay")
        if tx_type == "pay":
            return "pay_debt"
        elif tx_type == "new":
            debt_type = tool_args.get("debt_type", "personal_loan")
            if debt_type == "mortgage":
                return "add_mortgage"
            return "add_loan"
        return "pay_debt"

    # Fallback
    return sub_type or "other"


def build_messages_from_history(history: List[dict]) -> List[BaseMessage]:
    """Convert stored history to LangChain messages."""
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    return messages


async def execute_tool(tool_name: str, tool_args: dict, state: AgentState) -> dict:
    """Execute a tool by name with auto-fill defaults."""
    # Auto-fill defaults for domain-specific tools
    if tool_name in ("asset_transaction", "debt_transaction", "record_income", "record_expense"):
        tool_args = auto_fill_defaults(tool_name, tool_args, state)

    tool_fn = None
    for tool in CHAT_TOOLS:
        if tool.name == tool_name:
            tool_fn = tool
            break

    if tool_fn is None:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    try:
        result = await tool_fn.ainvoke(tool_args)
        return result
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message using the router agent.

    Args:
        request: ChatRequest with message and user context

    Returns:
        ChatResponse with classification and response
    """
    try:
        # Get or create conversation for ID tracking
        conversation = conversation_store.get_or_create(
            request.conversation_id,
            request.user_id
        )

        # Check if this is a follow-up in existing conversation
        existing_sub_type = getattr(conversation, 'sub_type', None)
        existing_action = getattr(conversation, 'action', None)

        # Build initial state
        initial_state: AgentState = {
            "message": request.message,
            "user_id": request.user_id,
            "conversation_id": conversation.id,
            "auth_token": request.auth_token,
            "api_base_url": request.api_base_url,
            "sub_type": existing_sub_type,  # Use existing if follow-up
            "action": existing_action,
            "confidence": 1.0 if existing_sub_type else 0.0,
            "default_cash_id": None,
            "default_cash_name": None,
            "messages": [],
            "executed_actions": [],
            "task_completed": False,
            "iteration": 0,
            "preview_action": None,
            "preview_data": None,
            "response": None,
            "error": None,
        }

        # Run the graph (router will skip if follow-up with existing sub_type)
        if existing_sub_type:
            logger.info(f"Follow-up message, existing context: {existing_sub_type}/{existing_action}")
        result = await agent_graph.ainvoke(initial_state)

        return ChatResponse(
            message=result.get("response", "Something went wrong."),
            conversation_id=conversation.id if not result.get("task_completed") and not result.get("preview_action") else None,
            sub_type=result.get("sub_type"),
            action=result.get("action"),
            task_completed=result.get("task_completed", False),
            executed_actions=result.get("executed_actions", []),
            preview_action=result.get("preview_action"),
            preview_data=result.get("preview_data"),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return ChatResponse(
            message="Sorry, something went wrong. Please try again.",
            conversation_id=request.conversation_id,
            task_completed=False,
            error=str(e),
        )
