from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
import logging

from schemas import RunwayRequest, RunwayResponse
from agents import calculate_runway


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=RunwayResponse)
async def runway_projection(request: RunwayRequest) -> RunwayResponse:
    """
    Calculate runway projection using AI agent.

    Takes user's financial data and returns:
    - AI assumptions (inflation, growth rates per asset)
    - Withdrawal strategy
    - Year-by-year projection
    - Milestones and suggestions
    """
    try:
        logger.info(f"Calculating runway for {len(request.assets)} assets, {len(request.debts)} debts")

        result = await calculate_runway(request)

        logger.info(f"Runway calculated: {result.runway_years} years ({result.runway_status})")

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error calculating runway: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate runway: {str(e)}")
