from .inflation import get_inflation_rate
from .stock_growth import get_stock_growth
from .debt_calc import calculate_debt_payoff
from .api_client import set_api_client, get_api_client, clear_api_client
from .api_tools import (
    list_assets,
    list_debts,
    asset_transaction,
    debt_transaction,
    record_income,
    record_expense,
    CHAT_TOOLS,
)

__all__ = [
    # Existing tools
    "get_inflation_rate",
    "get_stock_growth",
    "calculate_debt_payoff",
    # API client
    "set_api_client",
    "get_api_client",
    "clear_api_client",
    # Chat tools (domain-specific)
    "list_assets",
    "list_debts",
    "asset_transaction",
    "debt_transaction",
    "record_income",
    "record_expense",
    "CHAT_TOOLS",
]
