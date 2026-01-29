from typing import List, Dict, Optional, Any, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum

class BlockType(str, Enum):
    WORD = "WORD"
    LINE = "LINE"

class BoundingBox(BaseModel):
    x0: float
    top: float
    x1: float
    bottom: float
    page_number: int

class RawBlock(BaseModel):
    id: str = Field(..., description="Unique ID for tracing, e.g. 'p1_w0'")
    text: str
    bbox: BoundingBox
    block_type: BlockType
    source: Literal["pdf_text", "docling_ocr", "paddleocr", "mixed"]
    confidence: float = 1.0

class TableRow(BaseModel):
    cells: List[Optional[str]]

class Table(BaseModel):
    id: str
    page_number: int
    bbox: BoundingBox
    rows: List[TableRow]
    is_safe: bool = Field(True)

class MetricValue(BaseModel):
    year: str
    period: str
    value: float

class InterpretedMetric(BaseModel):
    name: str
    values: List[MetricValue]
    confidence: float
    source_block_ids: List[str]
    is_derived: bool = Field(True)

class FullTextBlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FOOTER_HEADER = "footer_header"
    IMAGE = "image"
    FORMULA = "formula"
    CODE = "code"
    KEY_VALUE = "key_value"
    UNKNOWN = "unknown"

class FullTextBlock(BaseModel):
    type: FullTextBlockType
    text: Union[str, List[str]]
    bbox: BoundingBox = Field(..., exclude=True)
    page_number: int
    source_block_ids: List[str] = Field(..., exclude=True)
    source: str = Field("mixed", exclude=True)
    confidence: float = 1.0
    structured_data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    children: Optional[List["FullTextBlock"]] = Field(None, description="Nested child blocks")

class FullTextPage(BaseModel):
    page_number: int
    blocks: List[FullTextBlock]

class FullTextExtraction(BaseModel):
    pages: List[FullTextPage]

class DocMetadata(BaseModel):
    filename: str
    page_count: int
    file_hash: str
    processing_time_seconds: float

class DocResult(BaseModel):
    file_identity: str
    metadata: DocMetadata
    raw_extraction: List[RawBlock]
    full_text_extraction: Optional[FullTextExtraction] = None
    strict_tables: List[Table]
    interpreted_metrics: List[InterpretedMetric]
    interpretation_notes: List[str] = Field(default_factory=list)
    global_confidence: float = 1.0
