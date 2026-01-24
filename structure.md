# Firewise Runway Agent

AI-powered service for calculating financial runway projections using LangChain.

## Overview

**Runway** = How long your money lasts when passive income < expenses

This service receives financial data from `firewise-api`, uses AI + tools to research market data, and returns a year-by-year projection with actionable suggestions.

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Runtime | Python 3.11+ | Best LangChain support |
| Framework | FastAPI | Async, fast, auto OpenAPI docs |
| AI Framework | LangChain | Agent orchestration, tool calling |
| LLM | Custom OpenAI-compatible endpoint | User's existing endpoint |
| Stock Data | yfinance | Free historical stock data |
| Deployment | Railway | Internal networking with firewise-api |

## Directory Structure

```
firewise-runway-agent/
├── main.py                     # FastAPI entry point
├── config.py                   # Environment settings (pydantic-settings)
├── requirements.txt
├── .env.example
├── structure.md                # This file
│
├── schemas/
│   ├── __init__.py
│   ├── request.py              # RunwayRequest - input from firewise-api
│   └── response.py             # RunwayResponse - output to firewise-api
│
├── tools/
│   ├── __init__.py
│   ├── inflation.py            # get_inflation_rate(country)
│   ├── stock_growth.py         # get_stock_growth(ticker, years)
│   └── debt_calc.py            # calculate_debt_payoff(balance, rate, payment)
│
├── agents/
│   ├── __init__.py
│   └── runway_agent.py         # LangChain agent + system prompt
│
└── routes/
    ├── __init__.py
    └── runway.py               # POST /runway endpoint
```

## API Contract

### Endpoint

```
POST /runway
```

### Request (from firewise-api)

```json
{
  "assets": [
    {
      "id": "uuid-1",
      "name": "Vanguard Total Market",
      "type": "etf",
      "ticker": "VTI",
      "balance": 180000,
      "currency": "USD"
    },
    {
      "id": "uuid-2",
      "name": "Emergency Fund",
      "type": "cash",
      "ticker": null,
      "balance": 25000,
      "currency": "USD"
    },
    {
      "id": "uuid-3",
      "name": "Rental Property",
      "type": "real_estate",
      "ticker": null,
      "balance": 300000,
      "currency": "USD"
    }
  ],
  "debts": [
    {
      "id": "uuid-4",
      "name": "Mortgage",
      "debt_type": "mortgage",
      "current_balance": 280000,
      "interest_rate": 0.06,
      "monthly_payment": 1800
    },
    {
      "id": "uuid-5",
      "name": "Car Loan",
      "debt_type": "auto_loan",
      "current_balance": 15000,
      "interest_rate": 0.05,
      "monthly_payment": 400
    }
  ],
  "annual_passive_income": 26900,
  "annual_expenses": 34800,
  "net_worth": 225000,
  "currency": "USD"
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `assets` | array | All user assets with current balances |
| `assets[].id` | string | Unique identifier |
| `assets[].name` | string | User-defined asset name |
| `assets[].type` | enum | `cash`, `deposit`, `stock`, `etf`, `bond`, `real_estate`, `crypto`, `other` |
| `assets[].ticker` | string? | Stock/ETF ticker symbol (nullable) |
| `assets[].balance` | number | Current balance in preferred currency |
| `assets[].currency` | string | Currency code |
| `debts` | array | All active debts |
| `debts[].id` | string | Unique identifier |
| `debts[].name` | string | User-defined debt name |
| `debts[].debt_type` | enum | `mortgage`, `personal_loan`, `credit_card`, `student_loan`, `auto_loan`, `other` |
| `debts[].current_balance` | number | Remaining balance |
| `debts[].interest_rate` | number | Annual rate as decimal (0.06 = 6%) |
| `debts[].monthly_payment` | number | Monthly payment amount |
| `annual_passive_income` | number | Total annual passive income |
| `annual_expenses` | number | Living expenses only (excludes debt payments) |
| `net_worth` | number | Total assets - total debts |
| `currency` | string | User's preferred currency |

### Response (from agent)

```json
{
  "assumptions": {
    "inflation_rate": 0.035,
    "growth_rates": {
      "Vanguard Total Market": 0.10,
      "Emergency Fund": 0.0,
      "Rental Property": 0.03
    },
    "reasoning": "Using 3.5% inflation based on current US CPI trends. VTI shows 10% annualized growth over 5 years. Cash has 0% growth. Real estate appreciation estimated at 3%."
  },
  "strategy": {
    "withdrawal_order": ["Emergency Fund", "Vanguard Total Market"],
    "keep_assets": ["Rental Property"],
    "reasoning": "Withdraw from cash first (0% growth), then ETF. Keep rental property as it generates passive income and is illiquid."
  },
  "projection": [
    {
      "year": 0,
      "net_worth": 225000,
      "assets": 505000,
      "debts": 280000,
      "expenses": 56400,
      "passive_income": 26900,
      "gap": 29500,
      "notes": null
    },
    {
      "year": 1,
      "net_worth": 220000,
      "assets": 498000,
      "debts": 275000,
      "expenses": 58374,
      "passive_income": 26900,
      "gap": 31474,
      "notes": null
    },
    {
      "year": 3,
      "net_worth": 235000,
      "assets": 510000,
      "debts": 275000,
      "expenses": 62500,
      "passive_income": 26900,
      "gap": 30800,
      "notes": "Car loan paid off - expenses reduced by $4,800/year"
    }
  ],
  "milestones": [
    {
      "year": 3,
      "event": "Car loan paid off",
      "impact": "Annual expenses reduced by $4,800"
    },
    {
      "year": 5,
      "event": "Emergency Fund depleted",
      "impact": "Now withdrawing from Vanguard Total Market"
    },
    {
      "year": 25,
      "event": "Mortgage paid off",
      "impact": "Annual expenses reduced by $21,600"
    }
  ],
  "suggestions": [
    "Paying extra $500/month on your mortgage would pay it off 8 years earlier, extending runway by ~5 years.",
    "Your rental property provides 45% of passive income - maintaining it is critical for your runway.",
    "Consider keeping 6 months expenses in cash before depleting Emergency Fund entirely."
  ],
  "runway_years": 38,
  "runway_status": "finite"
}
```

#### Response Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `assumptions.inflation_rate` | number | Annual inflation rate used (decimal) |
| `assumptions.growth_rates` | object | Growth rate per asset name |
| `assumptions.reasoning` | string | AI explanation of assumptions |
| `strategy.withdrawal_order` | array | Asset names in withdrawal priority |
| `strategy.keep_assets` | array | Assets to never sell |
| `strategy.reasoning` | string | AI explanation of strategy |
| `projection` | array | Year-by-year financial state |
| `projection[].year` | number | Year number (0 = current) |
| `projection[].net_worth` | number | Assets - debts |
| `projection[].assets` | number | Total asset value |
| `projection[].debts` | number | Total debt balance |
| `projection[].expenses` | number | Annual expenses (after inflation) |
| `projection[].passive_income` | number | Annual passive income |
| `projection[].gap` | number | Expenses + debt payments - passive income |
| `projection[].notes` | string? | Notable events this year |
| `milestones` | array | Key events during projection |
| `suggestions` | array | Actionable advice (2-4 items) |
| `runway_years` | number | Years until net worth <= 0 |
| `runway_status` | enum | `infinite` (>=100yr), `finite`, `critical` (<10yr) |

## Agent Strategy

### How the Agent Works

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Financial data from firewise-api                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: RESEARCH MARKET DATA                                   │
│  ───────────────────────────────────────────────────────────────│
│  Agent calls tools to gather real data:                         │
│                                                                 │
│  → get_inflation_rate("US")                                     │
│    Returns hint for AI to use current knowledge                 │
│                                                                 │
│  → get_stock_growth("VTI", 5) for each asset with ticker        │
│    Returns: {"ticker": "VTI", "annualized_growth": 0.10}        │
│                                                                 │
│  → calculate_debt_payoff(280000, 0.06, 1800) for each debt      │
│    Returns: {"months_remaining": 300, "payoff_year": 2050}      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DECIDE ASSUMPTIONS                                     │
│  ───────────────────────────────────────────────────────────────│
│  AI reasons about rates for EACH asset:                         │
│                                                                 │
│  "Based on tool results:                                        │
│   - Inflation: 3.5% (current US trend)                          │
│   - Vanguard Total Market: 10% (VTI 5-year historical)          │
│   - Emergency Fund: 0% (cash)                                   │
│   - Rental Property: 3% (real estate appreciation)"             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: DECIDE WITHDRAWAL STRATEGY                             │
│  ───────────────────────────────────────────────────────────────│
│  AI decides order based on growth rates:                        │
│                                                                 │
│  "Withdrawal order (lowest growth first):                       │
│   1. Emergency Fund (0% growth) - sell first                    │
│   2. Vanguard Total Market (10% growth) - sell second           │
│                                                                 │
│   Keep forever:                                                 │
│   - Rental Property (generates income, illiquid)"               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: CALCULATE YEAR-BY-YEAR PROJECTION                      │
│  ───────────────────────────────────────────────────────────────│
│  For year = 0 to 100 (or until net_worth <= 0):                 │
│                                                                 │
│  a) expenses = base_expenses × (1 + inflation)^year             │
│                                                                 │
│  b) debt_payments = sum of active debt monthly_payment × 12     │
│                                                                 │
│  c) gap = expenses + debt_payments - passive_income             │
│                                                                 │
│  d) If gap > 0: withdraw from assets (following strategy)       │
│                                                                 │
│  e) Apply growth to remaining assets                            │
│                                                                 │
│  f) Process debt payoffs:                                       │
│     - If debt months_remaining <= 12: mark as paid              │
│     - Reduce annual debt payments accordingly                   │
│                                                                 │
│  g) If dividend-generating assets sold:                         │
│     - Reduce passive_income proportionally                      │
│                                                                 │
│  h) Record year state + any notes/milestones                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: GENERATE SUGGESTIONS                                   │
│  ───────────────────────────────────────────────────────────────│
│  AI analyzes projection and provides 2-4 actionable tips:       │
│                                                                 │
│  - Debt acceleration: "Pay extra $X to extend runway Y years"   │
│  - Asset protection: "Rental provides X% income - maintain it"  │
│  - Risk warning: "80% in stocks - consider bonds for stability" │
│  - Optimization: "Refinance mortgage to lower rate"             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: Complete projection + reasoning to firewise-api       │
└─────────────────────────────────────────────────────────────────┘
```

## Tools

### 1. get_inflation_rate

```python
@tool
def get_inflation_rate(country: str = "US") -> dict:
    """
    Get current inflation rate for a country.

    Args:
        country: Country code (US, UK, EU, etc.)

    Returns:
        Guidance for AI to determine appropriate rate
    """
    return {
        "country": country,
        "instruction": "Use your knowledge of current inflation rates for this country",
        "typical_range": "2-4% in normal conditions, may be higher during inflationary periods"
    }
```

### 2. get_stock_growth

```python
@tool
def get_stock_growth(ticker: str, years: int = 5) -> dict:
    """
    Get historical annualized growth rate for a stock/ETF using yfinance.

    Args:
        ticker: Stock symbol (e.g., "VTI", "AAPL", "SPY")
        years: Years of history to analyze (default 5)

    Returns:
        Historical annualized growth rate
    """
    import yfinance as yf
    from datetime import datetime, timedelta

    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)

        hist = stock.history(start=start_date, end=end_date)
        if len(hist) < 2:
            return {"ticker": ticker, "error": "Insufficient data"}

        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        annualized = (end_price / start_price) ** (1/years) - 1

        return {
            "ticker": ticker,
            "annualized_growth": round(annualized, 4),
            "years": years,
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2)
        }
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}
```

### 3. calculate_debt_payoff

```python
@tool
def calculate_debt_payoff(
    balance: float,
    annual_rate: float,
    monthly_payment: float
) -> dict:
    """
    Calculate when a debt will be paid off using amortization formula.

    Args:
        balance: Current debt balance
        annual_rate: Annual interest rate as decimal (0.06 = 6%)
        monthly_payment: Monthly payment amount

    Returns:
        Payoff timeline and total interest
    """
    import math

    if monthly_payment <= 0 or balance <= 0:
        return {"months_remaining": 0, "total_interest": 0, "payoff_year": 2025}

    monthly_rate = annual_rate / 12

    # No interest case
    if monthly_rate <= 0:
        months = math.ceil(balance / monthly_payment)
        return {
            "months_remaining": months,
            "total_interest": 0,
            "payoff_year": 2025 + (months // 12)
        }

    # Check if payment covers interest
    interest_portion = balance * monthly_rate
    if monthly_payment <= interest_portion:
        return {
            "error": "Payment doesn't cover interest",
            "months_remaining": -1
        }

    # Standard amortization formula
    months = -math.log(1 - (monthly_rate * balance) / monthly_payment) / math.log(1 + monthly_rate)
    months = math.ceil(months)

    total_paid = months * monthly_payment
    total_interest = total_paid - balance

    return {
        "months_remaining": months,
        "total_interest": round(total_interest, 2),
        "payoff_year": 2025 + (months // 12)
    }
```

## System Prompt

```python
RUNWAY_SYSTEM_PROMPT = """You are a financial planning AI assistant specializing in
retirement runway calculations. Your task is to determine how long a person's
money will last given their current financial situation.

## YOUR TASK

Given the user's financial data (assets, debts, passive income, expenses), you must:

1. **Research Market Data**
   - Call get_inflation_rate() to understand current inflation
   - Call get_stock_growth(ticker, 5) for EACH asset that has a ticker
   - Call calculate_debt_payoff() for EACH debt to find payoff timeline

2. **Decide Assumptions**
   Based on tool results, determine:
   - Inflation rate (from get_inflation_rate guidance + your knowledge)
   - Growth rate for EACH asset by name:
     * For assets with tickers: use get_stock_growth result
     * For cash/deposits: typically 0-2%
     * For real_estate: typically 2-4% appreciation
     * For crypto: use 0% (too volatile)
     * For bonds: typically 2-4%

3. **Determine Withdrawal Strategy**
   Decide which assets to sell first when covering the gap:
   - Generally: sell lowest-growth assets first
   - NEVER sell real_estate (illiquid + generates rental income)
   - Preserve high-growth assets as long as possible

4. **Calculate Year-by-Year Projection**
   For each year from 0 to 100 (or until net_worth <= 0):

   a) Apply inflation to expenses:
      expenses_year_n = base_expenses × (1 + inflation)^n

   b) Calculate annual debt payments from active debts

   c) Calculate gap:
      gap = expenses + debt_payments - passive_income

   d) If gap > 0: withdraw from assets following your strategy
      - Reduce asset balance by withdrawal amount
      - If asset fully depleted, move to next in order

   e) Apply growth to remaining assets:
      asset_balance = asset_balance × (1 + growth_rate)

   f) Check for debt payoffs:
      - Use months_remaining from calculate_debt_payoff
      - When paid: remove from debt payments, add milestone

   g) If dividend-generating assets (stocks/ETFs) are sold:
      - Reduce passive_income proportionally

5. **Generate Suggestions**
   Provide 2-4 actionable tips based on your analysis:
   - Debt acceleration opportunities
   - Asset protection warnings
   - Risk/allocation recommendations
   - Income optimization ideas

## OUTPUT FORMAT

Return a JSON object with this EXACT structure:

{
  "assumptions": {
    "inflation_rate": <number between 0 and 0.1>,
    "growth_rates": {
      "<asset_name>": <number>,
      ...for each asset
    },
    "reasoning": "<1-2 sentences explaining your choices>"
  },
  "strategy": {
    "withdrawal_order": ["<asset_name>", ...in order to sell],
    "keep_assets": ["<asset_name>", ...never sell],
    "reasoning": "<1-2 sentences explaining strategy>"
  },
  "projection": [
    {
      "year": <0, 1, 2, ...>,
      "net_worth": <number>,
      "assets": <number>,
      "debts": <number>,
      "expenses": <number after inflation>,
      "passive_income": <number>,
      "gap": <number>,
      "notes": <string or null>
    },
    ...for each year until net_worth <= 0 or year 100
  ],
  "milestones": [
    {"year": <number>, "event": "<description>", "impact": "<description>"},
    ...
  ],
  "suggestions": [
    "<actionable suggestion>",
    ...2-4 suggestions
  ],
  "runway_years": <number of years until net_worth <= 0>,
  "runway_status": "<'infinite' if >=100, 'critical' if <10, else 'finite'>"
}

## IMPORTANT RULES

1. ALWAYS call tools before making assumptions - don't guess stock returns
2. Growth rates are keyed by asset NAME (not type or ticker)
3. Round currency values to 2 decimal places
4. Round rates to 4 decimal places (0.0350 = 3.50%)
5. Include a note in projection when significant events occur
6. Be conservative but realistic in your estimates
7. runway_status must be exactly: "infinite", "finite", or "critical"
"""
```

## Environment Variables

```env
# .env.example

# LLM Configuration
OPENAI_API_BASE=https://your-custom-endpoint.com/v1
OPENAI_API_KEY=your-api-key
MODEL_NAME=gpt-4o

# Server Configuration
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO

# Optional: For development
DEBUG=false
```

## Dependencies

```txt
# requirements.txt

fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
langchain>=0.1.0
langchain-openai>=0.0.5
yfinance>=0.2.35
python-dotenv>=1.0.0
```

## Railway Deployment

### Service Configuration

```yaml
# railway.toml (optional)
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
```

### Environment Variables in Railway

**firewise-runway-agent service:**
```
OPENAI_API_BASE=https://your-custom-endpoint.com/v1
OPENAI_API_KEY=your-key
MODEL_NAME=gpt-4o
PORT=8000
```

**firewise-api service (add):**
```
RUNWAY_AGENT_URL=http://${{firewise-runway-agent.RAILWAY_PRIVATE_DOMAIN}}:8000
```

### Internal Networking

Railway provides free internal networking between services:
- `firewise-api` calls `firewise-runway-agent` via internal URL
- No external traffic = no egress costs
- Low latency (~1-5ms between services)

## Usage Flow

```
┌──────────────┐     GET /fire/runway      ┌──────────────┐
│              │ ◄──────────────────────── │              │
│  firewise-   │                           │  firewise-   │
│     web      │                           │     api      │
│              │ ────────────────────────► │              │
└──────────────┘     runway response       └──────────────┘
                                                  │
                                                  │ POST /runway
                                                  │ (internal network)
                                                  ▼
                                           ┌──────────────┐
                                           │  firewise-   │
                                           │   runway-    │
                                           │    agent     │
                                           └──────────────┘
                                                  │
                                                  │ LangChain Agent
                                                  │ + Tools
                                                  ▼
                                           ┌──────────────┐
                                           │   Custom     │
                                           │   OpenAI     │
                                           │  Endpoint    │
                                           └──────────────┘
```

## Caching Strategy (in firewise-api)

- Cache runway results for 24 hours per user
- Cache key: `runway:{user_id}`
- Invalidate on: asset/debt/flow changes (optional)
- Force refresh: `GET /fire/runway?force=true`

## Error Handling

| Error | Status | Response |
|-------|--------|----------|
| Invalid request | 400 | `{"error": "Invalid request data", "details": [...]}` |
| Agent timeout | 504 | `{"error": "Agent timeout - try again"}` |
| LLM error | 500 | `{"error": "AI service unavailable"}` |
| Tool error | 200 | Agent handles gracefully, uses defaults |

## Health Check

```
GET /health

Response:
{
  "status": "ok",
  "service": "firewise-runway-agent",
  "version": "1.0.0"
}
```
