import logging
from typing import List, Dict, Any, Literal
from enum import Enum
from .domain import RawBlock, BoundingBox

logger = logging.getLogger(__name__)

class DocType(str, Enum):
    INVOICE = "invoice"
    REPORT = "report"
    FORM = "form"
    GENERIC = "generic"

class ExtractionAction(str, Enum):
    NATIVE = "native"
    OCR_PADDLE = "ocr_paddle"
    OCR_DOCLING = "ocr_docling"
    RECOVERY = "recovery" # Combined native + OCR

class TextQualityScorer:
    """
    Evaluates the quality of native text extraction to decide if OCR is necessary.
    """
    @staticmethod
    def score_page(blocks: List[RawBlock], page_width: float = 612.0, page_height: float = 792.0) -> float:
        if not blocks:
            return 0.0
        
        # 1. Word/Char Density
        total_text = "".join([b.text for b in blocks if b.text])
        if len(total_text.strip()) < 20:
            return 0.1 # Very low text
            
        # 2. Bounding Box Coverage (Rough estimate of ink area)
        # In scanned docs, native text is often empty or tiny fragments at the top/bottom
        total_area = page_width * page_height
        text_bbox_area = sum([(b.bbox.x1 - b.bbox.x0) * (b.bbox.bottom - b.bbox.top) for b in blocks])
        coverage = text_bbox_area / total_area
        
        # 3. Gibberish Detection (Basic)
        # Scanned docs often have random character strings if they have bad embedded OCR
        # We can look for excessive non-alphanumeric chars
        alnum_count = sum(c.isalnum() for c in total_text)
        alnum_ratio = alnum_count / len(total_text) if len(total_text) > 0 else 0
        
        # Weights (Heuristic)
        # If alnum_ratio is very low (e.g. < 0.3), it's likely bad embedded OCR
        score = alnum_ratio * min(1.0, (len(total_text) / 100))
        
        return float(score)

class DocumentTypeDetector:
    """
    Lightweight classification based on keywords and layout.
    """
    @staticmethod
    def detect(text: str) -> DocType:
        text_lower = text.lower()
        keywords = {
            DocType.INVOICE: ["invoice", "bill to", "ship to", "purchase order", "amount due", "total due"],
            DocType.REPORT: ["summary", "introduction", "conclusion", "table of contents", "appendix"],
            DocType.FORM: ["first name", "last name", "date of birth", "ssn", "signature"],
        }
        
        for doc_type, kw_list in keywords.items():
            if any(kw in text_lower for kw in kw_list):
                return doc_type
                
        return DocType.GENERIC

class ExtractionPolicy:
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def decide_action(self, page_blocks: List[RawBlock], doc_type: DocType = DocType.GENERIC) -> ExtractionAction:
        score = TextQualityScorer.score_page(page_blocks)
        logger.info(f"Page text quality score: {score:.2f} (threshold: {self.threshold})")
        
        if score < self.threshold:
            # For invoices or forms, we are more aggressive with OCR
            if doc_type in [DocType.INVOICE, DocType.FORM]:
                return ExtractionAction.OCR_PADDLE
            return ExtractionAction.OCR_PADDLE
            
        return ExtractionAction.NATIVE

    def should_run_enrichment(self, doc_type: DocType) -> bool:
        # Always run enrichment for structured docs
        return True
