import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Any, Literal
from .domain import RawBlock, BlockType, BoundingBox
# Removed global pdf2image and numpy imports for dependency isolation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRStrategy(ABC):
    @abstractmethod
    def is_available(self) -> Tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def extract_page(self, file_path: str, page_number: int) -> List[RawBlock]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

# Global variable to cache the OCR engine
_GLOBAL_PADDLE_OCR = None

class PaddleOCRStrategy(OCRStrategy):
    def __init__(self):
        self.ocr_ready = False
        self._init_error = None
        
        # Check if libraries are importable, but don't load model yet
        try:
            import apolis_ai_tools.compat  # Compatibility Shim
            import paddleocr
            import pdf2image
            self.ocr_ready = True
        except ImportError:
             self._init_error = "paddleocr, or pdf2image not installed"

    @property
    def ocr_engine(self):
        global _GLOBAL_PADDLE_OCR
        if _GLOBAL_PADDLE_OCR is None:
            # Lazy Loading: Initialize only when accessed
            try:
                import os
                os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
                from paddleocr import PaddleOCR
                import logging
                logging.getLogger("ppocr").setLevel(logging.ERROR)
                
                _GLOBAL_PADDLE_OCR = PaddleOCR(
                    use_angle_cls=False,
                    enable_mkldnn=False, 
                    det_limit_side_len=736,
                    lang='en',
                    ocr_version='PP-OCRv4'
                )
            except Exception as e:
                raise RuntimeError(f"Failed to lazy load PaddleOCR: {e}")
        return _GLOBAL_PADDLE_OCR

    @property
    def name(self) -> str:
        return "paddleocr"

    def is_available(self) -> Tuple[bool, Optional[str]]:
        return self.ocr_ready, self._init_error

    def extract_page(self, file_path: str, page_number: int) -> List[RawBlock]:
        is_ready, err = self.is_available()
        if not is_ready:
            raise RuntimeError(f"OCR_ENGINE_UNAVAILABLE|{self.name}|{err}")

        if not is_ready:
            raise RuntimeError(f"OCR_ENGINE_UNAVAILABLE|{self.name}|{err}")

        target_dpi = 150 # OPTIMIZED: Reduced from 200
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(
                file_path,
                first_page=page_number,
                last_page=page_number,
                dpi=target_dpi
            )
        except Exception as e:
             raise RuntimeError(f"Image conversion failed for {self.name}: {str(e)}")
        
        if not images:
            return []
            
        img = images[0]
        max_dimension = 2500
        width, height = img.size
        processed_img = img
        scale_ratio = 1.0
        
        if width > max_dimension or height > max_dimension:
            scale_ratio = max_dimension / float(max(width, height))
            new_width = int(width * scale_ratio)
            new_height = int(height * scale_ratio)
            processed_img = img.resize((new_width, new_height), resample=3)
        
        import numpy as np
        img_array = np.ascontiguousarray(np.array(processed_img).astype("uint8"))
        
        try:
            result = self.ocr_engine.ocr(img_array)
        except Exception as e:
            raise RuntimeError(f"{self.name} execution failed: {str(e)}")
        
        blocks = []
        final_scale = (72.0 / target_dpi) * (1.0 / scale_ratio)
        
        if not result or result[0] is None:
            return []
            
        page_result = result[0]
        
        # Consistent block extraction logic (Simplified version of original _extract_paddle)
        if isinstance(page_result, dict):
            try:
                boxes = page_result.get('rec_boxes', [])
                texts = page_result.get('rec_texts', [])
                scores = page_result.get('rec_scores', [])
                
                for idx, (box, text, score) in enumerate(zip(boxes, texts, scores)):
                    if not text.strip(): continue
                    
                    if isinstance(box, np.ndarray): box = box.tolist()
                    if not isinstance(box, list) or len(box) < 1: continue
                         
                    if not isinstance(box[0], (list, tuple)):
                         box = [ [box[i], box[i+1]] for i in range(0, len(box), 2) ]
                    
                    xs = [pt[0] for pt in box]; ys = [pt[1] for pt in box]
                    
                    blocks.append(RawBlock(
                        id=f"{self.name}_p{page_number}_seq{idx}",
                        text=text,
                        bbox=BoundingBox(
                            x0=float(min(xs) * final_scale),
                            top=float(min(ys) * final_scale),
                            x1=float(max(xs) * final_scale),
                            bottom=float(max(ys) * final_scale),
                            page_number=page_number
                        ),
                        block_type=BlockType.LINE,
                        source=self.name,
                        confidence=float(score)
                    ))
            except Exception as e:
                logger.error(f"Dict processing failed in {self.name}: {e}")
        else:
            for idx, line in enumerate(page_result):
                coords = line[0]
                text_info = line[1]
                text = text_info[0]
                confidence = float(text_info[1])
                
                if not text.strip(): continue

                xs = [pt[0] for pt in coords]; ys = [pt[1] for pt in coords]
                
                blocks.append(RawBlock(
                    id=f"{self.name}_p{page_number}_seq{idx}",
                    text=text,
                    bbox=BoundingBox(
                        x0=float(min(xs) * final_scale),
                        top=float(min(ys) * final_scale),
                        x1=float(max(xs) * final_scale),
                        bottom=float(max(ys) * final_scale),
                        page_number=page_number
                    ),
                    block_type=BlockType.LINE,
                    source=self.name,
                    confidence=confidence
                ))
            
        return blocks

class OCRService:
    def __init__(self):
        self.strategies: List[OCRStrategy] = []
        # Register default strategies
        self.strategies.append(PaddleOCRStrategy())
        # Note: DoclingOCRStrategy is typically handled by DoclingLayoutService internals,
        # but we can wrap it if we want a unified standalone OCR call.

    def extract(self, strategy_name: str, file_path: str, page_number: int) -> List[RawBlock]:
        for s in self.strategies:
            if s.name == strategy_name:
                return s.extract_page(file_path, page_number)
        raise ValueError(f"OCR strategy '{strategy_name}' not found.")

    def get_available_strategies(self) -> List[str]:
        return [s.name for s in self.strategies if s.is_available()[0]]
