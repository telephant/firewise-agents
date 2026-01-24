from langchain.tools import tool
import math


@tool
def calculate_debt_payoff(
    balance: float,
    annual_rate: float,
    monthly_payment: float
) -> dict:
    """
    Calculate when a debt will be paid off using standard amortization.

    This tool calculates the number of months until a debt is fully paid,
    the total interest that will be paid, and the expected payoff year.

    Args:
        balance: Current debt balance (e.g., 280000)
        annual_rate: Annual interest rate as decimal (e.g., 0.06 for 6%)
        monthly_payment: Monthly payment amount (e.g., 1800)

    Returns:
        Payoff timeline including months remaining, total interest, and payoff year
    """
    # Validate inputs
    if balance <= 0:
        return {
            "months_remaining": 0,
            "total_interest": 0,
            "payoff_year": 2025,
            "status": "already_paid"
        }

    if monthly_payment <= 0:
        return {
            "error": "Monthly payment must be positive",
            "months_remaining": -1
        }

    monthly_rate = annual_rate / 12
    current_year = 2025  # Base year for calculations

    # No interest case (0% loans)
    if monthly_rate <= 0:
        months = math.ceil(balance / monthly_payment)
        return {
            "months_remaining": months,
            "total_interest": 0,
            "payoff_year": current_year + (months // 12),
            "payoff_month": months % 12,
            "status": "on_track"
        }

    # Check if payment covers interest
    monthly_interest = balance * monthly_rate
    if monthly_payment <= monthly_interest:
        return {
            "error": "Payment doesn't cover monthly interest",
            "monthly_interest": round(monthly_interest, 2),
            "monthly_payment": monthly_payment,
            "shortfall": round(monthly_interest - monthly_payment, 2),
            "months_remaining": -1,
            "status": "underwater"
        }

    # Standard amortization formula: n = -log(1 - (r * P) / M) / log(1 + r)
    # where P = principal, r = monthly rate, M = monthly payment
    try:
        months = -math.log(1 - (monthly_rate * balance) / monthly_payment) / math.log(1 + monthly_rate)
        months = math.ceil(months)
    except (ValueError, ZeroDivisionError):
        return {
            "error": "Unable to calculate - check inputs",
            "months_remaining": -1
        }

    # Calculate total interest paid
    total_paid = months * monthly_payment
    total_interest = total_paid - balance

    # Calculate payoff date
    payoff_years = months // 12
    payoff_months = months % 12

    return {
        "months_remaining": months,
        "years_remaining": round(months / 12, 1),
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_paid, 2),
        "payoff_year": current_year + payoff_years,
        "payoff_month": payoff_months,
        "status": "on_track"
    }
