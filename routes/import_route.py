import logging
from fastapi import APIRouter, HTTPException

from schemas.import_schema import ImportRequest, ImportResponse
from agents.import_agent import analyze_import


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ImportResponse)
async def import_assets(request: ImportRequest):
    """
    Analyze a brokerage statement file and extract asset holdings.

    The file should be base64 encoded. Supported formats:
    - PDF (.pdf)
    - CSV (.csv)
    - Excel (.xlsx)

    Returns extracted assets for user preview before creation.
    """
    logger.info(f"Received import request: file_type={request.file_type}, file_name={request.file_name}")

    # Validate file size (10MB limit)
    try:
        import base64
        content_size = len(base64.b64decode(request.file_content))
        if content_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 10MB."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file content: {str(e)}"
        )

    try:
        result = await analyze_import(request)
        logger.info(f"Import analysis complete: {len(result.assets)} assets found, confidence={result.confidence}")
        return result
    except Exception as e:
        logger.error(f"Import analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze file: {str(e)}"
        )
