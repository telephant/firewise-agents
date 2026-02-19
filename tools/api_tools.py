"""
API Tools for Chat Agent

LangChain tools that call firewise-api domain-specific endpoints.
Each domain has its own transaction API:
- Assets: /fire/assets/transaction (invest, sell, transfer, add)
- Debts: /fire/debts/transaction (create, pay)
- Income: /fire/income
- Expense: /fire/expense
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from .api_client import get_api_client

logger = logging.getLogger(__name__)


# =============================================================================
# Asset Tools
# =============================================================================


@tool
async def list_assets() -> dict:
    """
    Get user's assets. Returns id, name, type, ticker, currency, balance.
    Use to find existing assets or verify holdings.
    """
    try:
        client = get_api_client()
        result = await client.get("/fire/assets")

        # Simplify response - only keep essential fields
        if result.get("success") and result.get("data", {}).get("assets"):
            simplified = []
            for a in result["data"]["assets"]:
                simplified.append({
                    "id": a["id"],
                    "name": a["name"],
                    "type": a["type"],
                    "ticker": a.get("ticker"),
                    "currency": a["currency"],
                    "balance": a.get("balance", 0),
                })
            return {"success": True, "assets": simplified}
        return result
    except Exception as e:
        logger.error(f"list_assets error: {e}")
        return {"success": False, "error": str(e)}


@tool
async def asset_transaction(
    transaction_type: str,
    amount: float,
    ticker: Optional[str] = None,
    shares: Optional[float] = None,
    asset_type: Optional[str] = None,
    from_asset_id: Optional[str] = None,
    to_asset_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Execute asset transaction. This is the main tool for investment operations.

    transaction_type options:
      - 'invest': Buy stocks/ETFs/crypto/bonds. Requires ticker, shares, amount.
      - 'sell': Sell investments. Requires ticker or from_asset_id, shares, amount.
      - 'transfer': Move money between accounts. Requires from_asset_id, to_asset_id, amount.
      - 'add': Create new asset with initial balance. Requires name or ticker, amount.

    Parameters:
      - ticker: Stock/ETF/crypto symbol (e.g., 'AAPL', 'BTC')
      - shares: Number of shares/units
      - asset_type: 'stock', 'etf', 'crypto', 'bond', 'cash', 'deposit', 'real_estate'
      - from_asset_id: Source asset ID (for sell/transfer)
      - to_asset_id: Destination asset ID (for transfer, sell proceeds)
      - name: Asset name (for add)
    """
    try:
        client = get_api_client()
        data = {
            "type": transaction_type,
            "amount": amount,
        }

        if ticker:
            data["ticker"] = ticker
        if shares is not None:
            data["shares"] = shares
        if asset_type:
            data["asset_type"] = asset_type
        if from_asset_id:
            data["from_asset_id"] = from_asset_id
        if to_asset_id:
            data["to_asset_id"] = to_asset_id
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        result = await client.post("/fire/assets/transaction", data)
        return result
    except Exception as e:
        logger.error(f"asset_transaction error: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Debt Tools
# =============================================================================


@tool
async def list_debts() -> dict:
    """Get user's debts. Returns id, name, type, balance only."""
    try:
        client = get_api_client()
        result = await client.get("/fire/debts")

        if result.get("success") and result.get("data", {}).get("debts"):
            simplified = []
            for d in result["data"]["debts"]:
                simplified.append({
                    "id": d["id"],
                    "name": d["name"],
                    "type": d["debt_type"],
                    "balance": d.get("current_balance"),
                })
            return {"success": True, "debts": simplified}
        return result
    except Exception as e:
        logger.error(f"list_debts error: {e}")
        return {"success": False, "error": str(e)}


@tool
async def debt_transaction(
    transaction_type: str,
    amount: float,
    name: Optional[str] = None,
    debt_type: Optional[str] = None,
    interest_rate: Optional[float] = None,
    term_months: Optional[int] = None,
    debt_id: Optional[str] = None,
    from_asset_id: Optional[str] = None,
    disburse_to_asset_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Execute debt transaction.

    transaction_type options:
      - 'create': Create new debt. Requires name, amount (principal).
      - 'pay': Make debt payment. Requires debt_id, amount.

    For 'create':
      - name: Debt name (e.g., 'Home Mortgage')
      - debt_type: 'mortgage', 'personal_loan', 'credit_card', 'student_loan', 'auto_loan'
      - interest_rate: Annual interest rate (e.g., 6.5)
      - term_months: Loan term in months (e.g., 360 for 30 years)
      - disburse_to_asset_id: Optional cash account to receive loan proceeds

    For 'pay':
      - debt_id: ID of debt to pay (get from list_debts)
      - from_asset_id: Cash account for payment
    """
    try:
        client = get_api_client()
        data = {
            "type": transaction_type,
            "amount": amount,
        }

        # Create fields
        if name:
            data["name"] = name
        if debt_type:
            data["debt_type"] = debt_type
        if interest_rate is not None:
            data["interest_rate"] = interest_rate
        if term_months is not None:
            data["term_months"] = term_months
        if disburse_to_asset_id:
            data["disburse_to_asset_id"] = disburse_to_asset_id

        # Pay fields
        if debt_id:
            data["debt_id"] = debt_id
        if from_asset_id:
            data["from_asset_id"] = from_asset_id
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        result = await client.post("/fire/debts/transaction", data)
        return result
    except Exception as e:
        logger.error(f"debt_transaction error: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Income Tool
# =============================================================================


@tool
async def record_income(
    category: str,
    amount: float,
    to_asset_id: str,
    from_asset_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Record income.

    Categories: salary, bonus, dividend, interest, freelance, gift, rental, capital_gains, refund

    Parameters:
      - category: Income category
      - amount: Income amount
      - to_asset_id: Cash account receiving income
      - from_asset_id: Optional source (e.g., stock for dividend, deposit for interest)
      - description: Optional description
    """
    try:
        client = get_api_client()
        data = {
            "category": category,
            "amount": amount,
            "to_asset_id": to_asset_id,
        }

        if from_asset_id:
            data["from_asset_id"] = from_asset_id
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        result = await client.post("/fire/income", data)
        return result
    except Exception as e:
        logger.error(f"record_income error: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Expense Tool
# =============================================================================


@tool
async def record_expense(
    category: str,
    amount: float,
    from_asset_id: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Record expense.

    Parameters:
      - category: Expense category (e.g., 'groceries', 'dining', 'utilities', 'entertainment')
      - amount: Expense amount
      - from_asset_id: Cash account paying the expense
      - description: Optional description
    """
    try:
        client = get_api_client()
        data = {
            "category": category,
            "amount": amount,
            "from_asset_id": from_asset_id,
        }

        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata

        result = await client.post("/fire/expense", data)
        return result
    except Exception as e:
        logger.error(f"record_expense error: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# Tool Registry
# =============================================================================

# Domain-specific tools
CHAT_TOOLS = [
    list_assets,
    list_debts,
    asset_transaction,
    debt_transaction,
    record_income,
    record_expense,
]
