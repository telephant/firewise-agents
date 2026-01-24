from pydantic import BaseModel
from typing import List, Dict, Optional, Literal


class Assumptions(BaseModel):
    inflation_rate: float
    growth_rates: Dict[str, float]  # asset_name -> growth_rate
    reasoning: str


class Strategy(BaseModel):
    withdrawal_order: List[str]  # asset names in order to sell
    keep_assets: List[str]  # asset names to never sell
    reasoning: str


class YearProjection(BaseModel):
    year: int
    net_worth: float
    assets: float
    debts: float
    expenses: float
    passive_income: float
    gap: float
    notes: Optional[str] = None


class Milestone(BaseModel):
    year: int
    event: str
    impact: str


RunwayStatus = Literal["infinite", "finite", "critical"]


class RunwayResponse(BaseModel):
    assumptions: Assumptions
    strategy: Strategy
    projection: List[YearProjection]
    milestones: List[Milestone]
    suggestions: List[str]
    runway_years: int
    runway_status: RunwayStatus
