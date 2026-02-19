"""
Chat Agent Prompts

Router prompt for classification and task-specific prompts for execution.
Uses domain-specific APIs: asset_transaction, debt_transaction, record_income, record_expense.
Args marked [DEFAULT] are auto-filled, [ASK] need user input.

IMPORTANT: When all required data is collected, call the tool IMMEDIATELY.
The system will show a preview to the user for confirmation.
Do NOT ask for text confirmation - just call the tool.
"""

# =============================================================================
# ROUTER PROMPT
# =============================================================================

ROUTER_PROMPT = """Classify the user's financial request. Reply JSON only.

TYPES (sub_type -> action):
- stock, etf, crypto, bond -> buy or sell
- salary, bonus, dividend, interest, freelance, gift, rental, capital_gains, refund -> null
- expense -> null
- transfer -> null
- mortgage, personal_loan, credit_card, student_loan, auto_loan -> new or payment
- cash, deposit, real_estate -> add

INFER INTENT: Use your knowledge. Standalone input without explicit action:
- Ticker symbol -> buy
- Expense category (groceries, rent, etc) -> expense
- Debt type mention -> new

PARSE: $=USD, 5k=5000, 1m=1000000

{"sub_type": "...", "action": "...", "confidence": 0.0-1.0}"""


# =============================================================================
# TASK PROMPTS
# =============================================================================

TASK_PROMPTS = {
    # ----------------------
    # BUY - asset_transaction(type='invest')
    # ----------------------
    "stock_buy": """Record stock purchase.

asset_transaction(
  transaction_type='invest',  # [DEFAULT]
  ticker=[ASK],               # e.g. 'AAPL'
  shares=[ASK],               # number of shares
  amount=[ASK],               # total cost in USD
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "etf_buy": """Record ETF purchase.

asset_transaction(
  transaction_type='invest',  # [DEFAULT]
  ticker=[ASK],               # e.g. 'QQQ', 'SPY'
  shares=[ASK],               # number of shares
  amount=[ASK],               # total cost in USD
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "crypto_buy": """Record crypto purchase.

asset_transaction(
  transaction_type='invest',  # [DEFAULT]
  ticker=[ASK],               # e.g. 'BTC', 'ETH'
  shares=[ASK],               # amount of crypto
  amount=[ASK],               # total cost in USD
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "bond_buy": """Record bond purchase.

asset_transaction(
  transaction_type='invest',  # [DEFAULT]
  ticker=[ASK],               # bond name
  shares=[ASK],               # face value or units
  amount=[ASK],               # total cost in USD
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # SELL - asset_transaction(type='sell')
    # ----------------------
    "stock_sell": """Record stock sale.

asset_transaction(
  transaction_type='sell',    # [DEFAULT]
  ticker=[ASK],               # e.g. 'AAPL'
  shares=[ASK],               # number of shares to sell
  amount=[ASK],               # total sale proceeds in USD
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "etf_sell": """Record ETF sale.

asset_transaction(
  transaction_type='sell',    # [DEFAULT]
  ticker=[ASK],               # e.g. 'QQQ', 'SPY'
  shares=[ASK],               # number of shares to sell
  amount=[ASK],               # total sale proceeds in USD
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "crypto_sell": """Record crypto sale.

asset_transaction(
  transaction_type='sell',    # [DEFAULT]
  ticker=[ASK],               # e.g. 'BTC', 'ETH'
  shares=[ASK],               # amount of crypto to sell
  amount=[ASK],               # total sale proceeds in USD
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    "bond_sell": """Record bond sale.

asset_transaction(
  transaction_type='sell',    # [DEFAULT]
  ticker=[ASK],               # bond name
  shares=[ASK],               # face value or units to sell
  amount=[ASK],               # total sale proceeds in USD
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have ticker, shares, and amount, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # INCOME - record_income
    # ----------------------
    "salary": """Record salary income.

record_income(
  category='salary',          # [DEFAULT]
  amount=[ASK],               # salary amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "bonus": """Record bonus income.

record_income(
  category='bonus',           # [DEFAULT]
  amount=[ASK],               # bonus amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "dividend": """Record dividend income.

record_income(
  category='dividend',        # [DEFAULT]
  amount=[ASK],               # dividend amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "interest": """Record interest income.

record_income(
  category='interest',        # [DEFAULT]
  amount=[ASK],               # interest amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "freelance": """Record freelance income.

record_income(
  category='freelance',       # [DEFAULT]
  amount=[ASK],               # freelance income amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "gift": """Record gift received.

record_income(
  category='gift',            # [DEFAULT]
  amount=[ASK],               # gift amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "rental": """Record rental income.

record_income(
  category='rental',          # [DEFAULT]
  amount=[ASK],               # rental income amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "capital_gains": """Record capital gains.

record_income(
  category='capital_gains',   # [DEFAULT]
  amount=[ASK],               # capital gains amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    "refund": """Record refund received.

record_income(
  category='refund',          # [DEFAULT]
  amount=[ASK],               # refund amount
  to_asset_id=[DEFAULT]       # auto-filled: default cash account
)

When you have the amount, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # EXPENSE - record_expense
    # ----------------------
    "expense": """Record expense.

record_expense(
  category=[ASK],             # e.g. 'groceries', 'dining', 'utilities'
  amount=[ASK],               # expense amount
  from_asset_id=[DEFAULT],    # auto-filled: default cash account
  description=[OPTIONAL]      # optional description
)

When you have category and amount, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # TRANSFER - asset_transaction(type='transfer')
    # ----------------------
    "transfer": """Record transfer between accounts.

1. Call list_assets to find accounts
2. asset_transaction(
  transaction_type='transfer', # [DEFAULT]
  amount=[ASK],                # transfer amount
  from_asset_id=[ASK],         # source account from list_assets
  to_asset_id=[ASK]            # destination account from list_assets
)

When you have amount and both account IDs, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # DEBT - NEW - debt_transaction(type='create')
    # ----------------------
    "mortgage_new": """Create new mortgage.

debt_transaction(
  transaction_type='create',  # [DEFAULT]
  name=[ASK],                 # e.g. 'Home Mortgage'
  debt_type='mortgage',       # [DEFAULT]
  amount=[ASK],               # loan amount (principal)
  interest_rate=[ASK],        # annual rate, e.g. 6.5
  term_months=[ASK]           # loan term, e.g. 360 for 30 years
)

When you have all required fields, call the tool immediately. User will confirm via UI.""",

    "personal_loan_new": """Create new personal loan.

debt_transaction(
  transaction_type='create',  # [DEFAULT]
  name=[ASK],                 # e.g. 'Personal Loan'
  debt_type='personal_loan',  # [DEFAULT]
  amount=[ASK],               # loan amount
  interest_rate=[ASK],        # annual rate
  term_months=[ASK]           # loan term in months
)

When you have all required fields, call the tool immediately. User will confirm via UI.""",

    "credit_card_new": """Create new credit card debt.

debt_transaction(
  transaction_type='create',  # [DEFAULT]
  name=[ASK],                 # e.g. 'Chase Sapphire'
  debt_type='credit_card',    # [DEFAULT]
  amount=[ASK],               # current balance
  interest_rate=[ASK]         # annual rate (APR)
)

When you have all required fields, call the tool immediately. User will confirm via UI.""",

    "student_loan_new": """Create new student loan.

debt_transaction(
  transaction_type='create',  # [DEFAULT]
  name=[ASK],                 # e.g. 'Federal Student Loan'
  debt_type='student_loan',   # [DEFAULT]
  amount=[ASK],               # loan amount
  interest_rate=[ASK],        # annual rate
  term_months=[ASK]           # loan term in months
)

When you have all required fields, call the tool immediately. User will confirm via UI.""",

    "auto_loan_new": """Create new auto loan.

debt_transaction(
  transaction_type='create',  # [DEFAULT]
  name=[ASK],                 # e.g. 'Car Loan'
  debt_type='auto_loan',      # [DEFAULT]
  amount=[ASK],               # loan amount
  interest_rate=[ASK],        # annual rate
  term_months=[ASK]           # loan term in months
)

When you have all required fields, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # DEBT - PAYMENT - debt_transaction(type='pay')
    # ----------------------
    "mortgage_payment": """Record mortgage payment.

1. Call list_debts to find the mortgage
2. debt_transaction(
  transaction_type='pay',     # [DEFAULT]
  amount=[ASK],               # payment amount
  debt_id=[ASK],              # mortgage ID from list_debts
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have amount and debt_id, call the tool immediately. User will confirm via UI.""",

    "personal_loan_payment": """Record personal loan payment.

1. Call list_debts to find the loan
2. debt_transaction(
  transaction_type='pay',     # [DEFAULT]
  amount=[ASK],               # payment amount
  debt_id=[ASK],              # loan ID from list_debts
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have amount and debt_id, call the tool immediately. User will confirm via UI.""",

    "credit_card_payment": """Record credit card payment.

1. Call list_debts to find the credit card
2. debt_transaction(
  transaction_type='pay',     # [DEFAULT]
  amount=[ASK],               # payment amount
  debt_id=[ASK],              # credit card ID from list_debts
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have amount and debt_id, call the tool immediately. User will confirm via UI.""",

    "student_loan_payment": """Record student loan payment.

1. Call list_debts to find the loan
2. debt_transaction(
  transaction_type='pay',     # [DEFAULT]
  amount=[ASK],               # payment amount
  debt_id=[ASK],              # loan ID from list_debts
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have amount and debt_id, call the tool immediately. User will confirm via UI.""",

    "auto_loan_payment": """Record auto loan payment.

1. Call list_debts to find the loan
2. debt_transaction(
  transaction_type='pay',     # [DEFAULT]
  amount=[ASK],               # payment amount
  debt_id=[ASK],              # loan ID from list_debts
  from_asset_id=[DEFAULT]     # auto-filled: default cash account
)

When you have amount and debt_id, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # ASSET - ADD - asset_transaction(type='add')
    # ----------------------
    "cash_add": """Add new cash account.

asset_transaction(
  transaction_type='add',     # [DEFAULT]
  name=[ASK],                 # account name, e.g. 'Chase Checking'
  asset_type='cash',          # [DEFAULT]
  amount=[ASK]                # initial balance
)

When you have name and amount, call the tool immediately. User will confirm via UI.""",

    "deposit_add": """Add new deposit/savings account.

asset_transaction(
  transaction_type='add',     # [DEFAULT]
  name=[ASK],                 # account name, e.g. 'High Yield Savings'
  asset_type='deposit',       # [DEFAULT]
  amount=[ASK]                # initial balance
)

When you have name and amount, call the tool immediately. User will confirm via UI.""",

    "real_estate_add": """Add new real estate property.

asset_transaction(
  transaction_type='add',     # [DEFAULT]
  name=[ASK],                 # property name, e.g. 'Primary Home'
  asset_type='real_estate',   # [DEFAULT]
  amount=[ASK]                # property value
)

When you have name and amount, call the tool immediately. User will confirm via UI.""",

    # ----------------------
    # UNKNOWN
    # ----------------------
    "unknown": """I couldn't understand your request. Please tell me:
- Buy/sell: "Buy 10 AAPL for $1500" or "Sell 5 QQQ for $2000"
- Income: "Got paid $5000 salary" or "Received $100 dividend"
- Expense: "Spent $50 on groceries"
- Transfer: "Transfer $1000 from checking to savings"
- Debt: "Add mortgage $500k at 6.5%" or "Pay $2000 to mortgage"
""",
}


def get_task_prompt(sub_type: str, action: str = None) -> str:
    """Get prompt for sub_type and action."""
    if action:
        key = f"{sub_type}_{action}"
    else:
        key = sub_type

    return TASK_PROMPTS.get(key, TASK_PROMPTS["unknown"])


# Legacy compatibility
def get_prompt(action_type: str) -> str:
    """Legacy function."""
    mapping = {
        "invest": "stock_buy",
        "dividend": "dividend",
        "interest": "interest",
        "income": "salary",
        "debt": "credit_card_new",
        "loan": "personal_loan_new",
        "mortgage": "mortgage_new",
    }
    key = mapping.get(action_type, "unknown")
    return TASK_PROMPTS.get(key, TASK_PROMPTS["unknown"])


ACTION_PROMPTS = TASK_PROMPTS
CHAT_SYSTEM_PROMPT = TASK_PROMPTS["stock_buy"]
