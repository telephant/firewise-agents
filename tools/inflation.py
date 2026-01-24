from langchain.tools import tool


@tool
def get_inflation_rate(country: str = "US") -> dict:
    """
    Get current inflation rate guidance for a country.

    Use this tool to understand what inflation rate to apply in projections.
    The tool provides guidance, and you should use your knowledge of current
    economic conditions to determine the appropriate rate.

    Args:
        country: Country code (US, UK, EU, JP, etc.)

    Returns:
        Guidance for determining appropriate inflation rate
    """
    # Provide hints based on country
    hints = {
        "US": {
            "country": "United States",
            "typical_range": "2-4%",
            "central_bank_target": "2%",
            "note": "Consider recent CPI data and Fed policy"
        },
        "UK": {
            "country": "United Kingdom",
            "typical_range": "2-4%",
            "central_bank_target": "2%",
            "note": "Consider Bank of England policy"
        },
        "EU": {
            "country": "European Union",
            "typical_range": "2-3%",
            "central_bank_target": "2%",
            "note": "Consider ECB policy"
        },
        "JP": {
            "country": "Japan",
            "typical_range": "0-2%",
            "central_bank_target": "2%",
            "note": "Historically low inflation"
        }
    }

    country_upper = country.upper()
    if country_upper in hints:
        return {
            **hints[country_upper],
            "instruction": "Use your knowledge of current economic conditions to determine the appropriate inflation rate"
        }

    return {
        "country": country,
        "typical_range": "2-4%",
        "instruction": "Use your knowledge of current economic conditions for this country"
    }
