from typing import Optional, List, Literal
from pydantic import BaseModel, Field


AssetType = Literal["stock", "etf", "bond", "crypto", "cash", "deposit", "real_estate", "other"]


class ExtractedAsset(BaseModel):
    """A single asset extracted from a brokerage statement."""
    name: str = Field(..., description="Full company or fund name")
    type: AssetType = Field(..., description="Asset type classification")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol if available")
    shares: float = Field(..., description="Number of shares or units held")
    currency: str = Field("USD", description="Trading currency")
    market: Optional[str] = Field(None, description="Exchange (e.g., NASDAQ, NYSE)")
    current_price: Optional[float] = Field(None, description="Current price per share if available")
    total_value: Optional[float] = Field(None, description="Total value (shares × price)")
    confidence: float = Field(1.0, description="Confidence score 0-1 for this extraction")


class SourceInfo(BaseModel):
    """Information about the source document."""
    broker: Optional[str] = Field(None, description="Detected broker name")
    statement_date: Optional[str] = Field(None, description="Statement date if found")
    account_type: Optional[str] = Field(None, description="Account type (e.g., Individual, IRA)")


class ImportRequest(BaseModel):
    """Request to analyze a brokerage statement file."""
    file_content: str = Field(..., description="Base64 encoded file content")
    file_type: Literal["pdf", "csv", "xlsx"] = Field(..., description="File type")
    file_name: Optional[str] = Field(None, description="Original file name for context")


class ImportResponse(BaseModel):
    """Response from the import analysis."""
    assets: List[ExtractedAsset] = Field(default_factory=list, description="List of extracted assets")
    source_info: SourceInfo = Field(default_factory=SourceInfo, description="Source document info")
    warnings: List[str] = Field(default_factory=list, description="Any parsing issues or warnings")
    confidence: float = Field(1.0, description="Overall extraction confidence 0-1")
