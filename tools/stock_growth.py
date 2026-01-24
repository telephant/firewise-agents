from langchain.tools import tool
import yfinance as yf
from datetime import datetime, timedelta


@tool
def get_stock_growth(ticker: str, years: int = 5) -> dict:
    """
    Get historical annualized growth rate for a stock or ETF.

    This tool fetches real historical data from Yahoo Finance to calculate
    the annualized return over the specified period.

    Args:
        ticker: Stock or ETF symbol (e.g., "VTI", "AAPL", "SPY", "QQQ")
        years: Number of years of history to analyze (default: 5)

    Returns:
        Historical annualized growth rate and price data
    """
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        hist = stock.history(start=start_date, end=end_date)

        if hist.empty or len(hist) < 2:
            return {
                "ticker": ticker,
                "error": "Insufficient historical data",
                "suggestion": "Use a conservative estimate (5-7% for stocks, 2-3% for bonds)"
            }

        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]

        # Calculate annualized return using CAGR formula
        actual_years = (hist.index[-1] - hist.index[0]).days / 365.25
        if actual_years < 0.5:
            return {
                "ticker": ticker,
                "error": "Less than 6 months of data available",
                "suggestion": "Use a conservative estimate"
            }

        annualized = (end_price / start_price) ** (1 / actual_years) - 1

        return {
            "ticker": ticker,
            "annualized_growth": round(annualized, 4),
            "years_analyzed": round(actual_years, 1),
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "start_date": hist.index[0].strftime("%Y-%m-%d"),
            "end_date": hist.index[-1].strftime("%Y-%m-%d")
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
            "suggestion": "Use a conservative estimate (5-7% for diversified stock funds)"
        }
