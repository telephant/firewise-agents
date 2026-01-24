"""
Test agent tools.
"""
import pytest
from tools import get_inflation_rate, get_stock_growth, calculate_debt_payoff


class TestInflationTool:
    """Tests for get_inflation_rate tool."""

    def test_us_inflation(self):
        """Test US inflation rate guidance."""
        result = get_inflation_rate.invoke({"country": "US"})

        assert result is not None
        assert "country" in result or "United States" in str(result)
        assert "instruction" in result

        print(f"\n  Inflation result: {result}")

    def test_unknown_country(self):
        """Test unknown country falls back to defaults."""
        result = get_inflation_rate.invoke({"country": "XYZ"})

        assert result is not None
        assert "instruction" in result

        print(f"\n  Unknown country result: {result}")


class TestStockGrowthTool:
    """Tests for get_stock_growth tool."""

    def test_vti_growth(self):
        """Test VTI (Vanguard Total Market) growth lookup."""
        result = get_stock_growth.invoke({"ticker": "VTI", "years": 5})

        assert result is not None
        assert "ticker" in result
        assert result["ticker"] == "VTI"

        if "error" not in result:
            assert "annualized_growth" in result
            # VTI should have some historical data
            assert isinstance(result["annualized_growth"], (int, float))
            print(f"\n  VTI growth: {result['annualized_growth']:.2%}")
        else:
            print(f"\n  VTI lookup error: {result.get('error')}")

    def test_spy_growth(self):
        """Test SPY (S&P 500) growth lookup."""
        result = get_stock_growth.invoke({"ticker": "SPY", "years": 5})

        assert result is not None
        assert "ticker" in result

        if "error" not in result:
            assert "annualized_growth" in result
            print(f"\n  SPY growth: {result['annualized_growth']:.2%}")
        else:
            print(f"\n  SPY lookup error: {result.get('error')}")

    def test_invalid_ticker(self):
        """Test invalid ticker returns error gracefully."""
        result = get_stock_growth.invoke({"ticker": "INVALIDTICKER123", "years": 5})

        assert result is not None
        assert "ticker" in result
        # Should have error or suggestion
        assert "error" in result or "suggestion" in result

        print(f"\n  Invalid ticker result: {result}")


class TestDebtCalcTool:
    """Tests for calculate_debt_payoff tool."""

    def test_mortgage_payoff(self):
        """Test typical mortgage payoff calculation."""
        result = calculate_debt_payoff.invoke({
            "balance": 280000,
            "annual_rate": 0.06,
            "monthly_payment": 1800
        })

        assert result is not None
        assert "months_remaining" in result
        assert result["months_remaining"] > 0
        assert "payoff_year" in result

        print(f"\n  Mortgage payoff: {result['months_remaining']} months")
        print(f"  Payoff year: {result['payoff_year']}")
        print(f"  Total interest: ${result.get('total_interest', 0):,.2f}")

    def test_car_loan_payoff(self):
        """Test car loan payoff calculation."""
        result = calculate_debt_payoff.invoke({
            "balance": 15000,
            "annual_rate": 0.05,
            "monthly_payment": 400
        })

        assert result is not None
        assert "months_remaining" in result
        assert result["months_remaining"] > 0

        print(f"\n  Car loan payoff: {result['months_remaining']} months")

    def test_zero_interest_loan(self):
        """Test 0% interest loan calculation."""
        result = calculate_debt_payoff.invoke({
            "balance": 10000,
            "annual_rate": 0,
            "monthly_payment": 500
        })

        assert result is not None
        assert result["months_remaining"] == 20  # 10000 / 500 = 20
        assert result["total_interest"] == 0

        print(f"\n  Zero interest payoff: {result['months_remaining']} months")

    def test_payment_too_low(self):
        """Test when payment doesn't cover interest."""
        result = calculate_debt_payoff.invoke({
            "balance": 100000,
            "annual_rate": 0.20,  # 20% rate
            "monthly_payment": 100  # Too low
        })

        assert result is not None
        assert "error" in result or result["months_remaining"] == -1

        print(f"\n  Payment too low result: {result}")

    def test_already_paid(self):
        """Test already paid debt."""
        result = calculate_debt_payoff.invoke({
            "balance": 0,
            "annual_rate": 0.06,
            "monthly_payment": 500
        })

        assert result is not None
        assert result["months_remaining"] == 0

        print(f"\n  Already paid result: {result}")
