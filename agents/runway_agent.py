import json
import re
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from config import settings
from schemas import RunwayRequest, RunwayResponse

logger = logging.getLogger(__name__)


RUNWAY_SYSTEM_PROMPT = """You calculate financial runway - how long until liquid assets are depleted.

CALCULATION METHOD:
1. Total Assets = sum of all asset balances (given in input)
2. Liquid Assets = Total Assets - real_estate (real estate is illiquid, cannot sell)
3. Each year:
   - annual_gap = (living_expenses × inflation^year) + (debt_payments × 12) - passive_income
   - If gap > 0: withdraw from liquid assets
   - Apply growth rates to remaining assets
   - Pay down debts: principal_paid = monthly_payment × 12 - (debt_balance × interest_rate)
4. runway_years = year when liquid_assets <= 0

Return ONLY valid JSON (no markdown):
{{
  "assumptions": {{
    "inflation_rate": 0.035,
    "growth_rates": {{"stock": 0.07, "etf": 0.07, "bond": 0.03, "cash": 0, "deposit": 0.02, "crypto": 0, "real_estate": 0.03}},
    "reasoning": "brief explanation"
  }},
  "strategy": {{
    "withdrawal_order": ["cash", "deposit", "bond", "stock"],
    "keep_assets": ["real_estate"],
    "reasoning": "brief explanation"
  }},
  "projection": [
    {{"year": 0, "net_worth": 500000, "assets": 600000, "debts": 100000, "expenses": 50000, "passive_income": 20000, "gap": 30000, "notes": null}}
  ],
  "milestones": [{{"year": 10, "event": "Mortgage paid off", "impact": "-12000/yr expenses"}}],
  "suggestions": ["Tip 1", "Tip 2"],
  "runway_years": 25,
  "runway_status": "finite"
}}

CRITICAL RULES:
- PASSIVE INCOME: Use the "Passive Income" value from input. Do NOT set to 0 if income is provided.
- TOTAL ASSETS: Sum all individual asset balances. Do NOT use net_worth as assets.
- DEBTS: Pay down each year using monthly_payment. Debt decreases over time.
- growth_rates: Use ASSET TYPES as keys (stock, etf, bond, cash, deposit, crypto, real_estate)
- If assets show [5y:X%,10y:Y%], use 5y rate. Otherwise use defaults: cash=0%, deposit=2%, stock/etf=7%, bond=3%, crypto=0%, real_estate=3%
- INFLATION: Based on region. Default 4% if unknown.
- projection: Show year 0, then every year until liquid assets depleted (or year 50 max).
- runway_status: "infinite" if 50+ years, "critical" if <10, else "finite"
- Never sell real_estate (illiquid)
"""


def format_request_for_agent(request: RunwayRequest) -> str:
    """Format the runway request as a compact prompt with assets grouped by type."""
    currency = request.currency

    # Group assets by type
    assets_by_type: dict[str, float] = {}
    for a in request.assets:
        assets_by_type[a.type] = assets_by_type.get(a.type, 0) + a.balance

    # Format as: stock=3500, etf=958, real_estate=467697, cash=3620, deposit=1000
    assets_summary = ", ".join([f"{t}={v:.0f}" for t, v in sorted(assets_by_type.items())])

    # Calculate totals
    total_assets = sum(a.balance for a in request.assets)
    total_debts = sum(d.current_balance for d in request.debts)
    liquid_assets = total_assets - assets_by_type.get("real_estate", 0)

    # Format debts
    debts = ", ".join([
        f"{d.name}={d.current_balance:.0f}@{d.interest_rate*100:.1f}%/{d.monthly_payment:.0f}mo"
        for d in request.debts
    ]) or "None"

    timezone_info = f"Region: {request.timezone}" if request.timezone else "Region: Unknown (use 4% inflation)"

    # Format monthly history as compact table (if available)
    monthly_history = ""
    if request.monthly_history:
        history_lines = [f"{m.month}: in={m.income:.0f}, ex={m.expenses:.0f}" for m in request.monthly_history]
        monthly_history = f"\nMonthly History: {'; '.join(history_lines)}"

    return f"""Currency: {currency}
Assets by Type: {assets_summary}
Total Assets: {total_assets:.0f} | Liquid Assets: {liquid_assets:.0f} (excludes real_estate)
Debts: {debts}
Total Debts: {total_debts:.0f}
Passive Income: {request.annual_passive_income:.0f}/yr
Living Expenses: {request.annual_expenses:.0f}/yr (does NOT include debt payments)
Net Worth: {request.net_worth:.0f}
{timezone_info}{monthly_history}

Calculate runway until liquid assets depleted. Return JSON only."""


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling various formats."""
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:500]}...")


async def calculate_runway(request: RunwayRequest) -> RunwayResponse:
    """
    Calculate runway projection using a single LLM call.

    Args:
        request: RunwayRequest with assets, debts, income, expenses, and growth rates

    Returns:
        RunwayResponse with projection, milestones, and suggestions
    """
    llm = ChatOpenAI(
        model=settings.model_name,
        openai_api_base=settings.openai_api_base,
        openai_api_key=settings.openai_api_key,
        temperature=0,
        max_tokens=4000,  # Ensure response isn't truncated
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", RUNWAY_SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    # Format input
    input_text = format_request_for_agent(request)
    logger.info(f"Runway input:\n{input_text}")

    # Single LLM call
    chain = prompt | llm
    result = await chain.ainvoke({"input": input_text})
    logger.info(f"Runway LLM response:\n{result.content}")

    # Parse JSON from response
    parsed = extract_json_from_response(result.content)
    logger.info(f"Parsed runway_years: {parsed.get('runway_years')}")

    # Validate and return as RunwayResponse
    return RunwayResponse(**parsed)
