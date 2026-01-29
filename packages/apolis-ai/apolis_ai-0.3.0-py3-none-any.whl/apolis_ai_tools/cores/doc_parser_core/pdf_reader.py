import hashlib
import time
# Removed global pdfplumber import for dependency isolation
import logging
from pathlib import Path
from typing import List
from .domain import DocMetadata, RawBlock, BlockType, BoundingBox
from .ocr_service import OCRService
from .extraction_policy import ExtractionPolicy, TextQualityScorer, DocumentTypeDetector, ExtractionAction, DocType

logger = logging.getLogger(__name__)

class PDFReader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.ocr_service = OCRService()
        self.policy = ExtractionPolicy(threshold=0.1) # OPTIMIZED: Favor Native Extraction
        self.doc_type = DocType.GENERIC
        self.baseline_line_count = 0
        
    def get_file_hash(self) -> str:
        sha256_hash = hashlib.sha256()
        with open(self.file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def read_metadata(self) -> DocMetadata:
        start_time = time.time()
        file_hash = self.get_file_hash()
        
        import pdfplumber
        try:
            with pdfplumber.open(self.file_path) as pdf:
                page_count = len(pdf.pages)
                return DocMetadata(
                    filename=self.file_path.name,
                    page_count=page_count,
                    file_hash=file_hash,
                    processing_time_seconds=time.time() - start_time
                )
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {str(e)}")

    def extract(self) -> List[RawBlock]:
        page_results = {} # page_num -> List[RawBlock]
        ocr_tasks = []

        import pdfplumber
        with pdfplumber.open(self.file_path) as pdf:
            # First pass: Lightweight sample for doc type detection (optional or use first page)
            sample_text = ""
            for p in pdf.pages[:3]:
                sample_text += (p.extract_text() or "")
            self.doc_type = DocumentTypeDetector.detect(sample_text)
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # Metric collection (avoid re-opening file later)
                p_text = page.extract_text()
                if p_text:
                    self.baseline_line_count += len(p_text.splitlines())

                # 1. Try native extraction
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                native_blocks = self._assemble_lines(words, page_num)
                
                # 2. Decide action based on policy
                action = self.policy.decide_action(native_blocks, self.doc_type)
                
                if action == ExtractionAction.OCR_PADDLE:
                    ocr_tasks.append((page_num, native_blocks))
                else:
                    page_results[page_num] = native_blocks
        
        # Parallel OCR (DISABLED: PaddleOCR C++ backend thread-safety issues causing crashes)
        # Reverted to sequential execution for stability.
        if ocr_tasks:
            for p, native_blocks in ocr_tasks:
                try:
                    res = self.ocr_service.extract("paddleocr", str(self.file_path), p)
                    if res:
                        page_results[p] = res
                        continue
                except Exception as e:
                    print(f"Warning: OCR fallback failed for page {p}: {e}")
                
                # Fallback
                page_results[p] = native_blocks
        
        # Flatten results in order
        final_blocks = []
        for p in sorted(page_results.keys()):
             final_blocks.extend(page_results[p])
             
        return final_blocks

    def _assemble_lines(self, words: List[dict], page_num: int) -> List[RawBlock]:
        if not words:
            return []
        
        sorted_words = sorted(words, key=lambda x: (x['top'], x['x0']))
        lines_on_page = []
        current_line = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            prev_word = current_line[-1]
            if abs(word['top'] - prev_word['top']) < 5: 
                 current_line.append(word)
            else:
                lines_on_page.append(current_line)
                current_line = [word]
        lines_on_page.append(current_line)
        
        blocks = []
        for i, line_words in enumerate(lines_on_page):
            x0 = min(w['x0'] for w in line_words)
            top = min(w['top'] for w in line_words)
            x1 = max(w['x1'] for w in line_words)
            bottom = max(w['bottom'] for w in line_words)
            text = " ".join(w['text'] for w in line_words)
            
            blocks.append(RawBlock(
                id=f"p{page_num}_l{i}",
                text=text,
                bbox=BoundingBox(
                    x0=float(x0), top=float(top), x1=float(x1), bottom=float(bottom), page_number=page_num
                ),
                block_type=BlockType.LINE,
                source="pdf_text",
                confidence=1.0
            ))
        return blocks
