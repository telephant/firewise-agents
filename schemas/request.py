from pydantic import BaseModel
from typing import List, Optional, Any


class Asset(BaseModel):
    id: str
    name: str
    type: str  # cash, deposit, stock, etf, bond, real_estate, crypto, other
    ticker: Optional[str] = None
    balance: float
    currency: str
    growth_rates: Optional[dict] = None  # {"5y": 0.12, "10y": 0.08}

    class Config:
        extra = "ignore"  # Ignore extra fields


class Debt(BaseModel):
    id: str
    name: str
    debt_type: str  # mortgage, personal_loan, credit_card, etc.
    current_balance: float
    interest_rate: float  # Annual rate as decimal (0.06 = 6%)
    monthly_payment: float

    class Config:
        extra = "ignore"


class MonthlyStats(BaseModel):
    """Compressed monthly income/expense totals."""
    month: str  # YYYY-MM format
    income: float
    expenses: float


class RunwayRequest(BaseModel):
    assets: List[Asset]
    debts: List[Debt]
    monthly_passive_income: float = 0
    monthly_expenses: float = 0
    monthly_gap: float = 0
    annual_passive_income: float
    annual_expenses: float
    annual_gap: float = 0
    monthly_history: List[MonthlyStats] = []  # Compressed monthly breakdown
    net_worth: float
    currency: str
    timezone: Optional[str] = None  # e.g., "Asia/Dubai", "America/New_York"

    class Config:
        extra = "ignore"
