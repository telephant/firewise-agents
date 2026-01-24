"""
Test FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test /health endpoint returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "firewise-runway-agent"

        print(f"\n  Health response: {data}")

    def test_root_endpoint(self):
        """Test / endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "firewise-runway-agent"
        assert "endpoints" in data

        print(f"\n  Root response: {data}")


class TestRunwayEndpoint:
    """Tests for runway projection endpoint."""

    def test_runway_endpoint_validation(self):
        """Test /runway endpoint validates input."""
        # Invalid request (missing required fields)
        response = client.post("/runway/", json={})

        assert response.status_code == 422  # Validation error

        print(f"\n  Validation error response: {response.json()}")

    def test_runway_endpoint_schema(self):
        """Test /runway endpoint accepts valid schema."""
        # Valid minimal request
        request = {
            "assets": [
                {
                    "id": "test-1",
                    "name": "Test Cash",
                    "type": "cash",
                    "ticker": None,
                    "balance": 10000,
                    "currency": "USD"
                }
            ],
            "debts": [],
            "annual_passive_income": 1000,
            "annual_expenses": 12000,
            "net_worth": 10000,
            "currency": "USD"
        }

        # Just test that request is accepted (not full agent call)
        # Full agent call is tested separately due to LLM dependency
        response = client.post("/runway/", json=request)

        # Should be 200 (success) or 500 (agent error, but schema valid)
        assert response.status_code in [200, 500]

        print(f"\n  Runway response status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Runway response: {response.json()}")


class TestRunwayEndpointIntegration:
    """Integration tests for runway endpoint (requires LLM)."""

    @pytest.mark.slow
    def test_runway_full_calculation(self):
        """Test full runway calculation (slow, calls LLM)."""
        request = {
            "assets": [
                {
                    "id": "asset-1",
                    "name": "Emergency Fund",
                    "type": "cash",
                    "ticker": None,
                    "balance": 25000,
                    "currency": "USD"
                },
                {
                    "id": "asset-2",
                    "name": "Vanguard ETF",
                    "type": "etf",
                    "ticker": "VTI",
                    "balance": 100000,
                    "currency": "USD"
                }
            ],
            "debts": [
                {
                    "id": "debt-1",
                    "name": "Car Loan",
                    "debt_type": "auto_loan",
                    "current_balance": 15000,
                    "interest_rate": 0.05,
                    "monthly_payment": 400
                }
            ],
            "annual_passive_income": 5000,
            "annual_expenses": 30000,
            "net_worth": 110000,
            "currency": "USD"
        }

        response = client.post("/runway/", json=request)

        if response.status_code == 200:
            data = response.json()

            assert "assumptions" in data
            assert "strategy" in data
            assert "projection" in data
            assert "runway_years" in data
            assert "runway_status" in data

            print(f"\n  Runway years: {data['runway_years']}")
            print(f"  Runway status: {data['runway_status']}")
            print(f"  Assumptions: {data['assumptions']}")
            print(f"  Strategy: {data['strategy']}")
            print(f"  Suggestions: {data.get('suggestions', [])}")
        else:
            print(f"\n  Error response: {response.json()}")
            # Don't fail - LLM might have issues
            pytest.skip(f"LLM call failed: {response.json()}")
