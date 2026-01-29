import sys
import json
import time
import traceback
# Removed global pdfplumber import for dependency isolation
from pathlib import Path
from .domain import BlockType
from .pdf_reader import PDFReader
from .layout import reconstruct_rows
from .layout_service import DoclingLayoutService

# Removed global _LAYOUT_SERVICE instantiation for dependency isolation
_LAYOUT_SERVICE = None

def get_layout_service():
    global _LAYOUT_SERVICE
    if _LAYOUT_SERVICE is None:
        from .layout_service import DoclingLayoutService
        _LAYOUT_SERVICE = DoclingLayoutService()
    return _LAYOUT_SERVICE

def process_document(input_file: str) -> dict:
    input_path = Path(input_file).resolve()
    
    if not input_path.exists():
        return {"error": f"File not found: {str(input_path)}", "status": "failed"}

    start_total_time = time.perf_counter()
    metrics = {
        "latencies": {},
        "quality": {}
    }

    try:
        t0 = time.perf_counter()
        reader = PDFReader(str(input_path))
        t1 = time.perf_counter()
        metrics["latencies"]["pdf_read_seconds"] = t1 - t0
        
        t0 = time.perf_counter()
        # Autonomous extraction (Policy-driven)
        raw_blocks = reader.extract()
        t1 = time.perf_counter()
        metrics["latencies"]["raw_extraction_seconds"] = t1 - t0
        
        t0 = time.perf_counter()
        line_blocks = [b for b in raw_blocks if b.block_type == BlockType.LINE]
        line_blocks = reconstruct_rows(line_blocks)
        
        processed_pages = set()
        total_extracted_lines = 0
        empty_line_count = 0
        duplicate_line_count = 0
        sources_seen = set()
        
        for b in line_blocks:
            pn = b.bbox.page_number
            processed_pages.add(pn)
            sources_seen.add(b.source)
            total_extracted_lines += 1
            if not b.text.strip():
                empty_line_count += 1
        
        extraction_mode = "mixed" if len(sources_seen) > 1 else (list(sources_seen)[0] if sources_seen else "unknown")

        # Duplicate detection
        page_texts = {}
        for b in line_blocks:
            pn = b.bbox.page_number
            if pn not in page_texts: page_texts[pn] = []
            page_texts[pn].append(b.text)
            
        for pn, texts in page_texts.items():
            counts = {}
            for t in texts: counts[t] = counts.get(t, 0) + 1
            duplicate_line_count += sum(c - 1 for c in counts.values() if c > 1)

        t1 = time.perf_counter()
        metrics["latencies"]["text_assembly_seconds"] = t1 - t0
        
        # Coverage Estimation
        baseline_count = getattr(reader, "baseline_line_count", 0)
        # Fallback if reader didn't capture it (e.g. cached reader?)
        if baseline_count == 0:
            import pdfplumber
            try:
                with pdfplumber.open(str(input_path)) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text()
                        if txt: baseline_count += len(txt.splitlines())
            except: pass
        
        metrics["quality"] = {
            "pages_processed": len(processed_pages),
            "total_lines_extracted": total_extracted_lines,
            "empty_line_count": empty_line_count,
            "duplicate_line_count": duplicate_line_count,
            "coverage_ratio": round(total_extracted_lines / baseline_count if baseline_count > 0 else 1.0, 4)
        }
        metrics["extraction_mode"] = extraction_mode
        
        final_output = {"extraction_metrics": metrics}
        
        # Enrichment is now authoritative and always runs
        t0 = time.perf_counter()
        # Use lazy-loaded service
        layout_service = get_layout_service()
        structured = layout_service.enrich(str(input_path), line_blocks)
        if structured and structured.pages:
            enrich_data = structured.model_dump(exclude_none=True)
            final_output.update(enrich_data)
        else:
            final_output["pages"] = []
            
        metrics["latencies"]["layout_enrichment_seconds"] = time.perf_counter() - t0
        metrics["latencies"]["total_pipeline_seconds"] = time.perf_counter() - start_total_time
        
        # Log critical perf metrics to server console
        print(f"\n[Perf] Total: {metrics['latencies']['total_pipeline_seconds']:.2f}s | "
              f"Docs(OCR?): {metrics['latencies'].get('raw_extraction_seconds',0):.2f}s | "
              f"Docling: {metrics['latencies'].get('layout_enrichment_seconds',0):.2f}s")

        return final_output

    except Exception as e:
        traceback.print_exc()
        return {
            "error": str(e),
            "status": "failed"
        }
