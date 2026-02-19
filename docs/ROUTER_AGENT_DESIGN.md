# Router Agent Design Document

## Overview

A two-stage LangGraph agent flow for processing financial chat requests:
1. **Router Stage**: Classify user intent → sub_type + action
2. **Task Stage**: Execute specific task with focused prompt + tools

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Message                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 1: ROUTER                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Router LLM (no tools, ~150 tokens)                     │    │
│  │  - Input: user message                                  │    │
│  │  - Output: {sub_type, action, confidence}               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  sub_type known? │
                    └─────────────────┘
                      │           │
                     YES          NO
                      │           │
                      ▼           ▼
              ┌───────────┐  ┌───────────────┐
              │  Stage 2  │  │ Ask user to   │
              │           │  │ clarify       │
              └───────────┘  └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 2: TASK EXECUTOR                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Task LLM (with tools, ~100-200 tokens prompt)          │    │
│  │  - Select prompt based on sub_type + action             │    │
│  │  - Bind relevant tools                                  │    │
│  │  - Execute tool loop                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Response to User                            │
└─────────────────────────────────────────────────────────────────┘
```

## Classification Types

### Main Categories & Sub Types

| Main | Sub Type | Actions | Description |
|------|----------|---------|-------------|
| **INVEST** | stock | buy, sell | Stock trading |
| | etf | buy, sell | ETF trading |
| | crypto | buy, sell | Cryptocurrency |
| | bond | buy, sell | Bonds |
| **INCOME** | salary | - | Monthly salary |
| | bonus | - | Performance bonus |
| | freelance | - | Contract work |
| | dividend | - | Stock dividends |
| | interest | - | Savings interest |
| | capital_gains | - | Investment gains |
| | gift | - | Money received |
| | rental | - | Rental income |
| | refund | - | Refunds |
| | other | - | Other income |
| **EXPENSE** | general | - | General spending |
| **TRANSFER** | between_accounts | - | Internal transfer |
| | to_savings | - | Deposit to savings |
| | from_savings | - | Withdraw from savings |
| **DEBT** | mortgage | new, payment | Home loan |
| | personal_loan | new, payment | Personal loan |
| | credit_card | new, payment | Credit card |
| | student_loan | new, payment | Student loan |
| | auto_loan | new, payment | Car loan |
| **ASSET** | cash | - | Cash account |
| | deposit | - | Savings account |
| | real_estate | - | Property |
| | other | - | Other assets |

## LangGraph State

```python
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    # Input
    message: str
    user_id: str
    conversation_id: Optional[str]
    auth_token: str
    api_base_url: str

    # Router output
    sub_type: Optional[str]
    action: Optional[str]
    confidence: Optional[float]

    # Task output
    messages: list  # LangChain messages
    executed_actions: list
    task_completed: bool

    # Final output
    response: Optional[str]
    error: Optional[str]
```

## LangGraph Flow

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("clarify", clarify_node)
workflow.add_node("task_executor", task_executor_node)

# Add edges
workflow.set_entry_point("router")
workflow.add_conditional_edges(
    "router",
    should_clarify,
    {
        "clarify": "clarify",
        "execute": "task_executor",
    }
)
workflow.add_edge("clarify", END)
workflow.add_edge("task_executor", END)

app = workflow.compile()
```

## Router Prompt

```
Classify the user's financial request.

TYPES:
- INVEST: stock, etf, crypto, bond (actions: buy, sell)
- INCOME: salary, bonus, freelance, dividend, interest, capital_gains, gift, rental, refund, other
- EXPENSE: general
- TRANSFER: between_accounts, to_savings, from_savings
- DEBT: mortgage, personal_loan, credit_card, student_loan, auto_loan (actions: new, payment)
- ASSET: cash, deposit, real_estate, other (action: add)

PARSING:
- $=USD, €=EUR, £=GBP, ¥=CNY
- 5k=5000, 1m=1000000
- Ticker → UPPERCASE
- "10个" = 10 shares

Reply JSON only:
{"sub_type": "stock", "action": "buy", "confidence": 0.95}

If unclear:
{"sub_type": "unknown", "action": null, "confidence": 0}
```

## Task Prompts

### Invest - Stock Buy
```
Record stock purchase.
Need: ticker, shares, total_cost
If missing info, ask ONE question.
Steps:
1. list_assets → find existing stock by ticker
2. If exists: update_asset(id, new_balance=old+shares, add_cost)
3. If not: create_asset(ticker, shares, total_cost)
Confirm before executing.
```

### Invest - Stock Sell
```
Record stock sale.
Need: ticker, shares, sale_price
Steps:
1. list_assets → find stock by ticker
2. If not found: "You don't have this stock"
3. update_asset(id, new_balance=old-shares)
4. create_flow(income, capital_gains, sale_price, from_asset_id=stock_id, to_asset_id=cash_id)
Confirm before executing.
```

### Income - Salary
```
Record salary income.
Need: amount, to which account (default: first cash account)
Steps:
1. list_assets → find cash accounts
2. create_flow(income, salary, amount, to_asset_id)
Confirm before executing.
```

### Income - Dividend
```
Record dividend income.
Need: amount, from which stock, to which account
Steps:
1. list_assets → find stocks and cash accounts
2. create_flow(income, dividend, amount, from_asset_id=stock_id, to_asset_id=cash_id)
Confirm before executing.
```

### Debt - Mortgage New
```
Create new mortgage.
Need: name, principal, interest_rate, term_months
Steps:
1. create_debt(name, mortgage, principal, interest_rate, term_months)
Confirm before executing.
```

### Debt - Mortgage Payment
```
Record mortgage payment.
Need: amount, which mortgage
Steps:
1. list_debts → find mortgages
2. create_flow(expense, debt_payment, amount, from_asset_id=cash_id, debt_id)
3. Update debt balance
Confirm before executing.
```

## Tool Registry

```python
# Tools available for task executor
TASK_TOOLS = {
    # Asset operations
    "invest": [list_assets, create_asset, update_asset],

    # Income/expense operations
    "income": [list_assets, create_flow],
    "expense": [list_assets, create_flow],
    "transfer": [list_assets, create_flow],

    # Debt operations
    "debt": [list_debts, create_debt, update_debt, list_assets, create_flow],

    # Asset creation
    "asset": [create_asset],
}
```

## Conversation Management

- **New conversation**: Always run router first
- **Existing conversation**:
  - If same sub_type: continue task executor
  - If different sub_type: clear history, re-route
- **Conversation TTL**: 30 minutes

## Token Estimation

| Stage | Tokens |
|-------|--------|
| Router prompt | ~150 |
| Router response | ~30 |
| Task prompt | ~100-200 |
| Task response | ~50-200 |
| **Total per request** | ~330-580 |

**vs Old approach**: ~2000+ tokens per request

**Savings**: ~70-80%

## Error Handling

1. **Router fails to parse**: Ask user to clarify
2. **Unknown sub_type**: Ask user to specify what they want to do
3. **Tool execution fails**: Return error message, don't retry
4. **Missing required info**: Ask user for specific missing field

## File Structure

```
firewise-agents/
├── agents/
│   └── chat_agent.py      # LangGraph agent implementation
├── prompts/
│   ├── router_prompt.py   # Router classification prompt
│   └── task_prompts.py    # Task-specific prompts
├── schemas/
│   └── chat_schema.py     # Request/response models
├── tools/
│   └── api_tools.py       # API calling tools
└── routes/
    └── chat.py            # FastAPI endpoint
```
