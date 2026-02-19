"""
Chat Agent Request/Response Schemas

Defines the data models for router agent flow.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal


# =============================================================================
# Classification Types
# =============================================================================

# Sub-types that the router can classify
SUB_TYPES = {
    # Invest
    "stock", "etf", "crypto", "bond",
    # Income
    "salary", "bonus", "freelance", "dividend", "interest",
    "capital_gains", "gift", "rental", "refund", "other_income",
    # Expense
    "general_expense",
    # Transfer
    "between_accounts", "to_savings", "from_savings",
    # Debt
    "mortgage", "personal_loan", "credit_card", "student_loan", "auto_loan",
    # Asset
    "cash", "deposit", "real_estate", "other_asset",
    # Unknown
    "unknown",
}

# Actions for specific sub-types
ACTIONS = {
    "buy", "sell",      # For invest
    "new", "payment",   # For debt
    "add",              # For asset
}


# =============================================================================
# Request Models
# =============================================================================

class ChatRequest(BaseModel):
    """Request to chat agent."""
    message: str = Field(..., description="User's message")
    user_id: str = Field(..., description="User ID for conversation tracking")
    conversation_id: Optional[str] = Field(
        None,
        description="Existing conversation ID (omit to start new)"
    )
    auth_token: str = Field(..., description="Bearer token for API calls")
    api_base_url: str = Field(
        default="http://localhost:3001",
        description="Base URL for firewise-api"
    )

    class Config:
        extra = "ignore"


# =============================================================================
# Router Models
# =============================================================================

class RouterResult(BaseModel):
    """Result from router classification."""
    sub_type: str = Field(..., description="Classified sub-type")
    action: Optional[str] = Field(None, description="Action (buy/sell/new/payment)")
    confidence: float = Field(default=1.0, description="Classification confidence")


# =============================================================================
# Response Models
# =============================================================================

class ExecutedAction(BaseModel):
    """An action that was executed by the agent."""
    tool: str = Field(..., description="Tool name that was called")
    args: dict = Field(default_factory=dict, description="Arguments passed")
    result: Any = Field(None, description="Result from the tool")
    success: bool = Field(True, description="Whether the action succeeded")


class PreviewData(BaseModel):
    """Data for preview mode (Main Stage Hijack)."""
    category: str = Field(..., description="Flow category (salary, dividend, expense, invest, etc.)")
    amount: Optional[float] = Field(None, description="Transaction amount")
    currency: Optional[str] = Field(None, description="Currency code (USD, etc.)")
    to_asset_id: Optional[str] = Field(None, description="Destination asset ID")
    from_asset_id: Optional[str] = Field(None, description="Source asset ID")
    debt_id: Optional[str] = Field(None, description="Debt ID for debt payments")
    description: Optional[str] = Field(None, description="Transaction description")
    shares: Optional[float] = Field(None, description="Number of shares for investments")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    date: Optional[str] = Field(None, description="Transaction date (YYYY-MM-DD)")


class ChatResponse(BaseModel):
    """Response from chat agent."""
    message: str = Field(..., description="Agent's response message")
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for follow-up messages"
    )
    sub_type: Optional[str] = Field(
        None,
        description="Classified sub-type from router"
    )
    action: Optional[str] = Field(
        None,
        description="Classified action from router"
    )
    task_completed: bool = Field(
        False,
        description="True if action was executed (conversation cleared)"
    )
    executed_actions: List[ExecutedAction] = Field(
        default_factory=list,
        description="Actions that were executed"
    )
    preview_action: Optional[Literal["preview"]] = Field(
        None,
        description="Set to 'preview' when agent is ready for user confirmation"
    )
    preview_data: Optional[PreviewData] = Field(
        None,
        description="Data for preview when preview_action='preview'"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if something went wrong"
    )


# =============================================================================
# LangGraph State
# =============================================================================

class AgentState(BaseModel):
    """State for LangGraph agent flow."""
    # Input
    message: str
    user_id: str
    conversation_id: Optional[str] = None
    auth_token: str
    api_base_url: str

    # Router output
    sub_type: Optional[str] = None
    action: Optional[str] = None
    confidence: float = 0.0

    # Task state
    messages: List[Any] = Field(default_factory=list)
    executed_actions: List[ExecutedAction] = Field(default_factory=list)
    task_completed: bool = False

    # Preview mode
    preview_action: Optional[str] = None
    preview_data: Optional[PreviewData] = None

    # Output
    response: Optional[str] = None
    error: Optional[str] = None

    class Config:
        extra = "allow"
