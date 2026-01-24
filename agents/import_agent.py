import base64
import io
import json
import re
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import settings
from schemas.import_schema import ImportRequest, ImportResponse, ExtractedAsset, SourceInfo


logger = logging.getLogger(__name__)


IMPORT_SYSTEM_PROMPT = """You are a financial document parser specializing in brokerage statements.

Extract asset holdings from the provided document text. For each asset found, extract:
- name: Full company or fund name (e.g., "Apple Inc.", "Vanguard S&P 500 ETF")
- type: One of [stock, etf, bond, crypto, cash, deposit, real_estate, other]
  - Use "etf" for ETFs, index funds, and mutual funds
  - Use "stock" for individual company stocks
  - Use "bond" for bonds and fixed income
  - Use "crypto" for cryptocurrencies
  - Use "cash" for cash holdings
  - Use "deposit" for money market or savings
- ticker: Stock symbol if available (e.g., "AAPL", "VOO")
- shares: Number of shares or units held (must be a number)
- currency: Trading currency (e.g., "USD", "EUR", "TWD")
- market: Exchange name if known (e.g., "NASDAQ", "NYSE", "TSE")
- current_price: Price per share if shown in document
- total_value: Total value if shown (or calculate as shares × price)
- confidence: Your confidence in this extraction (0.0 to 1.0)

Also extract source information:
- broker: Name of the brokerage if identifiable
- statement_date: Date of the statement if found (ISO format: YYYY-MM-DD)
- account_type: Type of account if mentioned (e.g., "Individual", "IRA", "401k")

Return ONLY valid JSON (no markdown):
{{
  "assets": [
    {{
      "name": "Apple Inc.",
      "type": "stock",
      "ticker": "AAPL",
      "shares": 100.0,
      "currency": "USD",
      "market": "NASDAQ",
      "current_price": 185.50,
      "total_value": 18550.0,
      "confidence": 0.95
    }}
  ],
  "source_info": {{
    "broker": "Schwab",
    "statement_date": "2024-01-15",
    "account_type": "Individual"
  }},
  "warnings": ["Some text was unclear"],
  "confidence": 0.9
}}

Rules:
- Only extract clear holdings, NOT pending orders, historical transactions, or dividends
- If a field is unclear, use null
- If shares count is missing but total value and price are available, calculate shares
- Be conservative - only include assets you're confident about
- Include a warning for any ambiguous or partially extracted data
- Set overall confidence based on document quality and extraction certainty
"""


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

                # Also try to extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        for row in table:
                            if row:
                                text_parts.append(" | ".join(str(cell) if cell else "" for cell in row))

        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_csv(content: bytes) -> str:
    """Extract text from CSV bytes using pandas, with fallback to raw text."""
    import pandas as pd

    # Try different encodings
    for encoding in ['utf-8', 'latin1', 'cp1252']:
        try:
            # First try pandas for clean CSVs
            df = pd.read_csv(io.BytesIO(content), encoding=encoding)
            return df.to_string()
        except UnicodeDecodeError:
            continue
        except Exception:
            # If pandas fails (irregular format), fall back to raw text
            try:
                text = content.decode(encoding)
                return text
            except UnicodeDecodeError:
                continue

    # Last resort: decode with errors ignored
    return content.decode('utf-8', errors='ignore')


def extract_text_from_excel(content: bytes) -> str:
    """Extract text from Excel bytes using pandas."""
    try:
        import pandas as pd

        # Read all sheets
        xlsx = pd.ExcelFile(io.BytesIO(content))
        text_parts = []

        for sheet_name in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=sheet_name)
            text_parts.append(f"=== Sheet: {sheet_name} ===")
            text_parts.append(df.to_string())

        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting Excel text: {e}")
        raise ValueError(f"Failed to extract text from Excel: {str(e)}")


def extract_text(file_content: str, file_type: str, file_name: Optional[str] = None) -> str:
    """Extract text from base64-encoded file content."""
    try:
        content = base64.b64decode(file_content)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {str(e)}")

    if file_type == "pdf":
        return extract_text_from_pdf(content)
    elif file_type == "csv":
        return extract_text_from_csv(content)
    elif file_type == "xlsx":
        return extract_text_from_excel(content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response, handling various formats."""
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from response: {text[:500]}...")


async def analyze_import(request: ImportRequest) -> ImportResponse:
    """
    Analyze a brokerage statement and extract asset holdings.

    Args:
        request: ImportRequest with base64 file content and file type

    Returns:
        ImportResponse with extracted assets and metadata
    """
    # Extract text from file
    try:
        document_text = extract_text(
            request.file_content,
            request.file_type,
            request.file_name
        )
    except ValueError as e:
        return ImportResponse(
            assets=[],
            source_info=SourceInfo(),
            warnings=[str(e)],
            confidence=0.0
        )

    if not document_text or len(document_text.strip()) < 50:
        return ImportResponse(
            assets=[],
            source_info=SourceInfo(),
            warnings=["Document appears to be empty or contains very little text"],
            confidence=0.0
        )

    # Truncate if too long (keep first 15000 chars to stay within token limits)
    max_chars = 15000
    truncated = False
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars]
        truncated = True

    # Create LLM chain
    llm = ChatOpenAI(
        model=settings.model_name,
        openai_api_base=settings.openai_api_base,
        openai_api_key=settings.openai_api_key,
        temperature=0.1,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", IMPORT_SYSTEM_PROMPT),
        ("human", "Document content:\n\n{document}\n\nExtract all asset holdings. Return JSON only."),
    ])

    chain = prompt | llm

    try:
        result = await chain.ainvoke({"document": document_text})
        parsed = extract_json_from_response(result.content)

        # Build response
        response = ImportResponse(
            assets=[ExtractedAsset(**a) for a in parsed.get("assets", [])],
            source_info=SourceInfo(**parsed.get("source_info", {})),
            warnings=parsed.get("warnings", []),
            confidence=parsed.get("confidence", 0.8)
        )

        if truncated:
            response.warnings.append("Document was truncated due to size. Some assets may be missing.")
            response.confidence = min(response.confidence, 0.7)

        return response

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        return ImportResponse(
            assets=[],
            source_info=SourceInfo(),
            warnings=[f"Analysis failed: {str(e)}"],
            confidence=0.0
        )
