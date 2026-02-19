"""
Chat Route

FastAPI endpoint for conversational financial data entry.
"""

import logging
from fastapi import APIRouter, HTTPException

from schemas import ChatRequest, ChatResponse
from agents import process_chat

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Conversational chat endpoint for recording financial data.

    The agent can:
    - Record income (salary, bonus, dividends, etc.)
    - Record expenses
    - Record transfers between accounts
    - Create new assets (accounts)
    - Create new debts (loans, mortgages)

    Authentication is passed through from the API service.
    """
    logger.info(f"Chat request: {request.message[:100]}...")

    # Validate auth token
    if not request.auth_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is required",
        )

    try:
        response = await process_chat(request)

        logger.info(f"Chat response: {response.message[:100]}...")
        logger.info(f"Executed actions: {len(response.executed_actions)}")

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat: {str(e)}",
        )


@router.get("/health")
async def chat_health():
    """Health check for chat endpoint."""
    return {"status": "ok", "service": "chat-agent"}
