import logging
import os

os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
logger = logging.getLogger(__name__)
from typing import List, Dict, Any, Optional
import traceback
from difflib import SequenceMatcher
from .domain import RawBlock, FullTextBlock, FullTextBlockType, BoundingBox, FullTextExtraction, FullTextPage

# Removed global docling imports for dependency isolation
DOCLING_AVAILABLE = None # Will be determined lazily


# Global instance for Singleton pattern
_GLOBAL_CONVERTER = None

def get_converter():
    global _GLOBAL_CONVERTER, DOCLING_AVAILABLE
    
    if DOCLING_AVAILABLE is None:
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
            from docling.datamodel.document import DocItemLabel
            DOCLING_AVAILABLE = True
        except ImportError:
            DOCLING_AVAILABLE = False
        except Exception:
            DOCLING_AVAILABLE = False

    if _GLOBAL_CONVERTER is None and DOCLING_AVAILABLE:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
        from docling.datamodel.document import DocItemLabel
        
        options = PdfPipelineOptions()
        # OPTIMIZED: Auto-detect GPU or use CPU with more threads
        options.accelerator_options = AcceleratorOptions(
            num_threads=int(os.environ.get("DOCLING_NUM_THREADS", 4)), 
            device=AcceleratorDevice.AUTO
        )
        options.do_ocr = False 
        
        # HEAVY OPERATION: Table structure is slow on CPU. Allow disabling it.
        enable_tables = os.environ.get("DOCLING_ENABLE_TABLES", "true").lower() in ["true", "1", "yes"]
        options.do_table_structure = enable_tables
        
        logging.getLogger("DoclingLayout").warning(
             f"Docling Config - Tables: {enable_tables} (Disable='false'), "
             f"Threads: {options.accelerator_options.num_threads}, "
             f"Device: {options.accelerator_options.device}"
        )

        options.images_scale = 1.0 # OPTIMIZED: Aggressive downscale (Standard 72 DPI)
        options.ocr_options.lang = ["en"]
        
        _GLOBAL_CONVERTER = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=options)
            }
        )
    return _GLOBAL_CONVERTER

class DoclingLayoutService:
    def __init__(self):
        self.converter = get_converter()


    def enrich(self, file_path: str, raw_blocks: List[RawBlock]) -> FullTextExtraction:
        if not self.converter:
            return FullTextExtraction(pages=[])

        try:
            result = self.converter.convert(file_path)
            pages_data: Dict[int, Dict[str, Any]] = {}
            doc = result.document
            
            raw_by_page: Dict[int, List[RawBlock]] = {}
            used_raw_ids = set()
            
            # Step 0: Fuzzy Duplicate Resolution (Deduplicate RawBlocks)
            deduplicated_raw = self._deduplicate_raw_blocks(raw_blocks)
            
            for rb in deduplicated_raw:
                pn = rb.bbox.page_number
                if pn not in raw_by_page: raw_by_page[pn] = []
                raw_by_page[pn].append(rb)

            # Optimization: Sort by Top coordinate for spatial pruning in the loop
            for pn in raw_by_page:
                raw_by_page[pn].sort(key=lambda b: b.bbox.top)

            for item_entry in doc.iterate_items():
                if isinstance(item_entry, tuple):
                    item, level = item_entry
                else:
                    item, level = item_entry, 0
                

                # Debug logging removed for performance


                item_label = getattr(item, "label", None)
                if item_label is None:
                    if "Text" in type(item).__name__: item_label = "text"
                    else:
                        if not hasattr(item, "prov") or not item.prov: continue
                        item_label = "unknown"

                if not hasattr(item, "prov") or not item.prov: continue
                prov = item.prov[0]
                page_no = prov.page_no
                
                # Coordinate Normalization
                page_height = 792.0
                if hasattr(doc, "pages") and page_no in doc.pages:
                    p_obj = doc.pages[page_no]
                    if hasattr(p_obj, "size"): page_height = p_obj.size.height
                
                v_origin = getattr(prov, "coord_origin", "BOTTOMLEFT")
                is_bottom_left = "BOTTOMLEFT" in str(v_origin)
                
                if is_bottom_left:
                    dl_bbox = BoundingBox(
                        x0=float(prov.bbox.l), top=float(page_height - prov.bbox.t),
                        x1=float(prov.bbox.r), bottom=float(page_height - prov.bbox.b),
                        page_number=page_no
                    )
                else:
                    dl_bbox = BoundingBox(
                        x0=float(prov.bbox.l), top=float(prov.bbox.t),
                        x1=float(prov.bbox.r), bottom=float(prov.bbox.b),
                        page_number=page_no
                    )

                label_map = {
                    DocItemLabel.TITLE: FullTextBlockType.HEADING,
                    DocItemLabel.SECTION_HEADER: FullTextBlockType.HEADING,
                    DocItemLabel.PARAGRAPH: FullTextBlockType.PARAGRAPH,
                    DocItemLabel.TEXT: FullTextBlockType.PARAGRAPH,
                    DocItemLabel.LIST_ITEM: FullTextBlockType.LIST_ITEM,
                    DocItemLabel.TABLE: FullTextBlockType.TABLE,
                    DocItemLabel.KEY_VALUE_REGION: FullTextBlockType.KEY_VALUE,
                    "text": FullTextBlockType.PARAGRAPH,
                }

                ft_type = label_map.get(item_label, FullTextBlockType.UNKNOWN)
                if ft_type == FullTextBlockType.UNKNOWN:
                    label_str = str(item_label).lower()
                    if "header" in label_str or "title" in label_str: ft_type = FullTextBlockType.HEADING
                    elif "table" in label_str: ft_type = FullTextBlockType.TABLE
                    elif "key_value" in label_str or "form" in label_str: ft_type = FullTextBlockType.KEY_VALUE
                    elif any(x in label_str for x in ["pic", "fig", "image"]): ft_type = FullTextBlockType.IMAGE
                    else: ft_type = FullTextBlockType.PARAGRAPH

                constituent_blocks = []
                if page_no in raw_by_page:
                    for rb in raw_by_page[page_no]:
                        # Optimization: Early exit if block is strictly below the target area
                        # padding is 15.0 in _is_contained
                        if rb.bbox.top > dl_bbox.bottom + 15.0:
                            break
                            
                        if self._is_contained(rb.bbox, dl_bbox):
                            constituent_blocks.append(rb)
                            used_raw_ids.add(rb.id)

                # Assemble high-fidelity text for heuristics
                text = getattr(item, "text", "").strip()
                if not text or (ft_type != FullTextBlockType.TABLE and len(text) < 20):
                    if constituent_blocks:
                        constituent_blocks.sort(key=lambda b: (b.bbox.top, b.bbox.x0))
                        paddle_text = "\n".join([b.text for b in constituent_blocks])
                        if len(paddle_text) > len(text): text = paddle_text

                # HEURISTIC: Fix TABLE/PARAGRAPH misclassified as IMAGE or UNKNOWN
                if (ft_type in [FullTextBlockType.IMAGE, FullTextBlockType.UNKNOWN]) and len(text) > 15:
                    lines = text.split('\n')
                    num_density = sum(c.isdigit() for c in text) / (len(text) + 1)
                    table_keywords = ["total", "subtotal", "revenue", "rate", "balance", "amount", "qty", "actual", "budget", "ytd", "paid", "due", "reimbursement", "expense", "hotel", "airfare"]
                    if num_density > 0.2 or any(kw in text.lower() for kw in ["total", "subtotal", "paid", "due", "amount"]):
                        ft_type = FullTextBlockType.TABLE
                        logger.info(f"Early re-classified {item_label} as TABLE: {text[:50]}...")
                    elif ":" in text and len(text.split(":")[0]) < 30:
                        ft_type = FullTextBlockType.KEY_VALUE
                        logger.info(f"Early re-classified {item_label} as KEY_VALUE: {text[:50]}...")
                    elif len(text) > 40 or len(lines) > 1:
                        ft_type = FullTextBlockType.PARAGRAPH
                        logger.info(f"Early re-classified {item_label} as PARAGRAPH: {text[:50]}...")
                
                # Assemble structured data
                structured_data = {}
                from docling.datamodel.document import TableItem, TextItem, PictureItem
                
                is_kv = isinstance(item, TextItem) and ft_type == FullTextBlockType.KEY_VALUE
                if isinstance(item, TableItem) or ft_type == FullTextBlockType.TABLE:
                    # ... (Existing table extraction logic)
                    pass # Placeholder for target content match
                elif is_kv or ft_type == FullTextBlockType.KEY_VALUE:
                    # Form/KV Extraction
                    kv_pairs = {}
                    if ":" in text:
                        for line in text.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                if len(k) < 30: kv_pairs[k.strip()] = v.strip()
                    if kv_pairs: structured_data["pairs"] = kv_pairs
                    try:
                        # 1. Native Export Attempts (Passing doc to avoid deprecation warnings)
                        md = ""
                        if hasattr(item, "export_to_markdown"):
                            md = item.export_to_markdown(doc=doc)
                            # Treat Docling's "Image not available" placeholder as empty to trigger our spatial fallback
                            if md and "Image not available" in md and "PdfPipelineOptions" in md:
                                md = ""
                        
                        df = None
                        if hasattr(item, "export_to_dataframe"):
                            df = item.export_to_dataframe(doc=doc)
                        
                        if df is not None:
                            if not df.columns.is_unique:
                                new_cols = []
                                counts = {}
                                for col in df.columns:
                                    col_str = str(col)
                                    counts[col_str] = counts.get(col_str, 0) + 1
                                    new_cols.append(f"{col_str}_{counts[col_str]-1}" if counts[col_str] > 1 else col_str)
                                df.columns = new_cols
                            structured_data["records"] = df.to_dict(orient="records")
                        
                        # Grid Reconstruction (Docling Native)
                        if hasattr(item, "data") and hasattr(item.data, "table_cells"):
                            table_cells = item.data.table_cells
                            m_row = max((getattr(c, "start_row_offset_idx", -1) for c in table_cells), default=-1)
                            m_col = max((getattr(c, "start_col_offset_idx", -1) for c in table_cells), default=-1)
                            if m_row >= 0 and m_col >= 0:
                                grid = [["" for _ in range(m_col + 1)] for _ in range(m_row + 1)]
                                for cell in table_cells:
                                    r_idx = getattr(cell, "start_row_offset_idx", -1)
                                    c_idx = getattr(cell, "start_col_offset_idx", -1)
                                    if r_idx >= 0 and c_idx >= 0:
                                        grid[r_idx][c_idx] = getattr(cell, "text", "")
                                if any(any(c_v for c_v in r_v) for r_v in grid):
                                    structured_data["grid"] = grid

                        # 2. SPATIAL FALLBACK: If native exports are empty but we have Paddle blocks
                        if (not md or not structured_data.get("records")) and constituent_blocks:
                            # Cluster into rows using Y tolerance
                            constituent_blocks.sort(key=lambda b: (b.bbox.top, b.bbox.x0))
                            rows = []
                            if constituent_blocks:
                                current_row = [constituent_blocks[0]]
                                for b in constituent_blocks[1:]:
                                    if abs(b.bbox.top - current_row[-1].bbox.top) < 10: # 10pt tolerance
                                        current_row.append(b)
                                    else:
                                        rows.append(current_row)
                                        current_row = [b]
                                rows.append(current_row)
                            
                            if rows:
                                # Simple Markdown & Records Generation
                                recovered_md = ""
                                recovered_records = []
                                for r_idx, row_blks in enumerate(rows):
                                    row_blks.sort(key=lambda b: b.bbox.x0)
                                    row_texts = [b.text for b in row_blks]
                                    recovered_md += "| " + " | ".join(row_texts) + " |\n"
                                    if r_idx == 0: recovered_md += "| " + "--- | " * len(row_texts) + "\n"
                                    recovered_records.append({str(i): txt for i, txt in enumerate(row_texts)})
                                
                                if not md: md = recovered_md
                                if "records" not in structured_data or not structured_data["records"]:
                                    structured_data["records"] = recovered_records
                            
                        structured_data["markdown"] = md if md else ""

                    except Exception as e:
                        logger.warning(f"High-fidelity table extraction failed: {e}")

                    # 3. Universal Key-Value Recovery (Fallback for Failed Tables)
                    # 3. Universal Key-Value Recovery (Fallback for Failed Tables)
                    width_check = 100
                    should_fallback = True
                    
                    if structured_data.get("records"):
                        should_fallback = False
                        rec = structured_data["records"]
                        if len(rec) > 0:
                            if len(rec[0]) < 2:
                                should_fallback = True

                    if should_fallback:
                         kv_pairs_fallback = {}
                         lines = text.split('\n')

                         kv_pairs_fallback = {}
                         lines = text.split('\n')
                         for line in lines:
                             delimiter = None
                             # Prioritize clear delimiters
                             if ":" in line: delimiter = ":"
                             elif "#" in line: delimiter = "#"
                             
                             if delimiter:
                                 parts = line.split(delimiter, 1)
                                 key = parts[0].strip()
                                 val = parts[1].strip()
                                 # Heuristic: Keys shouldn't be too long (e.g. not a sentence)
                                 if len(key) < 50 and val: 
                                     kv_pairs_fallback[key] = val
                             else:
                                 # Handle implicit delimiters (e.g. "INVOICE DATE 10/16/2025")
                                 if "INVOICE DATE" in line.upper():
                                     parts = line.upper().split("INVOICE DATE", 1)
                                     if len(parts) > 1: kv_pairs_fallback["INVOICE DATE"] = parts[1].strip()
                         
                         if kv_pairs_fallback:
                             structured_data["pairs"] = kv_pairs_fallback
                             ft_type = FullTextBlockType.KEY_VALUE
                             # Update the main text to be the KV string representation if it was truncated
                             logger.info(f"Fallback: Re-classified TABLE as KEY_VALUE. Found {len(kv_pairs_fallback)} pairs.")

                # PRESENTABILITY: Truncate long table text for cleaner JSON
                # PRESENTABILITY: Split table text into lines for cleaner JSON
                if ft_type == FullTextBlockType.TABLE:
                    text = text.split('\n')

                # Final fallback for empty tables
                if not text and ft_type == FullTextBlockType.TABLE:
                    text = structured_data.get("markdown", "Table Content")[:200]

                # Key-Value Pair Extraction (Only if not already structural)
                if ft_type == FullTextBlockType.KEY_VALUE:
                    if hasattr(item, "data") and hasattr(item.data, "key") and hasattr(item.data, "value"):
                        k_text = getattr(item.data.key, "text", "").strip()
                        v_text = getattr(item.data.value, "text", "").strip()
                        if k_text:
                            if "kv_pairs" not in structured_data: structured_data["kv_pairs"] = {}
                            structured_data["kv_pairs"][k_text] = v_text
                
                avg_confidence = 1.0
                if constituent_blocks:
                    avg_confidence = sum(b.confidence for b in constituent_blocks) / len(constituent_blocks)
                
                ft_block = FullTextBlock(
                    type=ft_type, text=text, bbox=dl_bbox, page_number=page_no,
                    source_block_ids=[b.id for b in constituent_blocks],
                    source="docling_ocr" if not constituent_blocks else "mixed",
                    confidence=avg_confidence,
                    structured_data=structured_data if structured_data else None,
                    metadata={
                        "level": level, 
                        "label": str(item_label).split(".")[-1],
                        "docling_prov": {
                            "bbox": prov.bbox.__dict__ if hasattr(prov, "bbox") else None,
                            "page_no": page_no,
                            "coord_origin": str(v_origin)
                        }
                    },
                    children=[]
                )

                # Hierarchical Nesting Logic
                if page_no not in pages_data:
                    pages_data[page_no] = {"roots": [], "stack": []}
                
                pg_info = pages_data[page_no]
                while pg_info["stack"] and pg_info["stack"][-1][0] >= level:
                    pg_info["stack"].pop()
                
                if pg_info["stack"]:
                    parent_block = pg_info["stack"][-1][1]
                    if parent_block.children is None: parent_block.children = []
                    parent_block.children.append(ft_block)
                else:
                    pg_info["roots"].append(ft_block)
                
                pg_info["stack"].append((level, ft_block))

            # RESIDUAL RECOVERY: No Word Left Behind
            # Any RawBlock that wasn't adopted by a Docling item should be added as a floating paragraph
            # ANTI-GHOSTING: Check if text is already present to avoid duplicates
            
            for pn in sorted(raw_by_page.keys()):
                orphans = [rb for rb in raw_by_page[pn] if rb.id not in used_raw_ids]
                if not orphans: continue
                
                # Build a quick lookup of existing text on this page
                existing_text_blob = ""
                if pn in pages_data:
                    def get_all_text(nodes):
                        t = ""
                        for n in nodes:
                            txt = n.text
                            if isinstance(txt, list):
                                txt = " ".join(txt)
                            t += " " + (txt or "")
                            if n.children: t += get_all_text(n.children)
                        return t
                    existing_text_blob = get_all_text(pages_data[pn]["roots"]).lower()

                # Filter orphans based on text presence
                true_orphans = []
                for o in orphans:
                    # If this specific text block is already in the page output, skip it
                    # Use a normalized check (strip limits false negatives)
                    clean_text = o.text.strip().lower()
                    if len(clean_text) > 5 and clean_text in existing_text_blob:
                        continue
                    true_orphans.append(o)
                
                if not true_orphans: continue

                # Cluster orphans into rough lines/blocks
                true_orphans.sort(key=lambda b: (b.bbox.top, b.bbox.x0))
                if pn not in pages_data: pages_data[pn] = {"roots": [], "stack": []}
                
                # Improved spatial clustering for residuals
                current_residual = [true_orphans[0]]
                for rb in true_orphans[1:]:
                    # If same page and reasonably close (30pt), group together for structural analysis
                    if abs(rb.bbox.top - current_residual[-1].bbox.top) < 30: 
                        current_residual.append(rb)
                    else:
                        self._add_residual_block(pages_data[pn]["roots"], current_residual, pn)
                        current_residual = [rb]
                self._add_residual_block(pages_data[pn]["roots"], current_residual, pn)

            # Post-processing: Final association for any missed floating text
            for p_no in sorted(pages_data.keys()):
                pg_info = pages_data[p_no]
                roots = pg_info["roots"]
                
                def _cleanup(blks):
                    for b in blks:
                        if not b.children: b.children = None
                        else: _cleanup(b.children)
                _cleanup(roots)

            pages = []
            for pn in sorted(pages_data.keys()):
                pages.append(FullTextPage(page_number=pn, blocks=pages_data[pn]["roots"]))
            
            return FullTextExtraction(pages=pages)

        except Exception as e:
            if "bad_alloc" in str(e) or "Conversion failed" in str(e):
                logger.error(f"Docling memory exhaustion or conversion failure: {e}. Falling back to basic extraction.")
            else:
                logger.exception("Docling layout enrichment failed")
            return self._fallback_enrich(raw_blocks)

    def _fallback_enrich(self, raw_blocks: List[RawBlock]) -> FullTextExtraction:
        """Robust fallback that clusters blocks into tables/paragraphs when Docling fails."""
        pages_data: Dict[int, List[RawBlock]] = {}
        for rb in raw_blocks:
            pn = rb.bbox.page_number
            if pn not in pages_data: pages_data[pn] = []
            pages_data[pn].append(rb)
        
        pages = []
        for pn in sorted(pages_data.keys()):
            blks = pages_data[pn]
            if not blks: continue
            
            # Sort by top-to-bottom
            blks.sort(key=lambda b: (b.bbox.top, b.bbox.x0))
            
            # Step 1: Cluster into lines
            lines = []
            if blks:
                current_line = [blks[0]]
                for b in blks[1:]:
                    if abs(b.bbox.top - current_line[-1].bbox.top) < 8: # 8pt tolerance
                        current_line.append(b)
                    else:
                        lines.append(current_line)
                        current_line = [b]
                lines.append(current_line)
            
            # Step 2: Identify structural clusters (Tables vs Paragraphs)
            ft_blocks = []
            i = 0
            while i < len(lines):
                line = lines[i]
                line_text = " ".join([b.text for b in line])
                
                # Check for table heuristics: consecutive lines with shared structure or high digit density
                potential_table_lines = [line]
                table_keywords = ["total", "subtotal", "revenue", "rate", "balance", "amount", "qty", "actual", "budget", "ytd"]
                
                def is_table_line(l):
                    t = " ".join([b.text for b in l]).lower()
                    digit_count = sum(c.isdigit() for c in t)
                    is_data = digit_count / (len(t) + 1) > 0.15
                    has_kw = any(kw in t for kw in table_keywords)
                    return is_data or has_kw or len(l) > 2

                if is_table_line(line):
                    # Peek ahead to collect the whole table
                    j = i + 1
                    while j < len(lines):
                        if is_table_line(lines[j]) or (len(lines[j]) <= 1 and len(" ".join([b.text for b in lines[j]])) < 5): # Allow sparse filler lines
                            potential_table_lines.append(lines[j])
                            j += 1
                        else:
                            break
                    
                    if len(potential_table_lines) >= 2 or (len(potential_table_lines) == 1 and len(line) > 3):
                        # Construct TABLE block
                        table_text = "\n".join([" ".join([b.text for b in l]) for l in potential_table_lines])
                        all_table_blks = [b for l in potential_table_lines for b in l]
                        
                        # Calculate BBox for the whole table
                        t_x0 = min(b.bbox.x0 for b in all_table_blks)
                        t_top = min(b.bbox.top for b in all_table_blks)
                        t_x1 = max(b.bbox.x1 for b in all_table_blks)
                        t_bot = max(b.bbox.bottom for b in all_table_blks)
                        
                        # Reconstruct records/markdown (simplistic)
                        recovered_md = ""
                        recovered_records = []
                        for r_idx, r_line in enumerate(potential_table_lines):
                            r_line.sort(key=lambda b: b.bbox.x0)
                            r_texts = [b.text for b in r_line]
                            recovered_md += "| " + " | ".join(r_texts) + " |\n"
                            if r_idx == 0: recovered_md += "| " + "--- | " * len(r_texts) + "\n"
                            recovered_records.append({str(k): v for k, v in enumerate(r_texts)})
                        
                        final_type = FullTextBlockType.TABLE
                        final_data = {"markdown": recovered_md, "records": recovered_records}

                        # Check if this "Table" is actually a Key-Value list (Header info)
                        if len(recovered_records) > 0 and len(recovered_records[0]) < 2:
                             kv_pairs_fallback = {}
                             lines = table_text.split('\n')
                             for line in lines:
                                 delimiter = None
                                 if ":" in line: delimiter = ":"
                                 elif "#" in line: delimiter = "#"
                                 
                                 if delimiter:
                                     parts = line.split(delimiter, 1)
                                     key = parts[0].strip()
                                     val = parts[1].strip()
                                     if len(key) < 50 and val: 
                                         kv_pairs_fallback[key] = val
                                 elif "INVOICE DATE" in line.upper(): # Implicit date handler
                                     parts = line.upper().split("INVOICE DATE", 1)
                                     if len(parts) > 1: kv_pairs_fallback["INVOICE DATE"] = parts[1].strip()

                             if kv_pairs_fallback:
                                 final_type = FullTextBlockType.KEY_VALUE
                                 final_data["pairs"] = kv_pairs
                        
                        final_text = table_text[:400] + "... [Fallback Table]" if len(table_text) > 400 else table_text
                        if final_type == FullTextBlockType.TABLE:
                            final_text = table_text.split('\n')
                        
                        ft_blocks.append(FullTextBlock(
                            type=final_type,
                            text=final_text,
                            bbox=BoundingBox(x0=t_x0, top=t_top, x1=t_x1, bottom=t_bot, page_number=pn),
                            page_number=pn,
                            source_block_ids=[b.id for b in all_table_blks],
                            source="mixed",
                            confidence=0.9, # Heuristic confidence
                            structured_data=final_data
                        ))
                        i = j
                        continue

                # Default to Heading or Paragraph
                b_source_ids = [b.id for b in line]
                l_bbox = line[0].bbox # Simplified
                l_type = FullTextBlockType.PARAGRAPH
                if len(line) == 1 and len(line_text) < 60:
                    l_type = FullTextBlockType.HEADING # Simple title heuristic
                
                ft_blocks.append(FullTextBlock(
                    type=l_type,
                    text=line_text,
                    bbox=l_bbox,
                    page_number=pn,
                    source_block_ids=b_source_ids,
                    source=line[0].source,
                    confidence=line[0].confidence
                ))
                i += 1
            
            pages.append(FullTextPage(page_number=pn, blocks=ft_blocks))
        
        return FullTextExtraction(pages=pages)

    def _add_residual_block(self, roots: List[FullTextBlock], blks: List[RawBlock], pn: int):
        """Creates a TABLE or PARAGRAPH for orphaned OCR data using spatial clustering."""
        if not blks: return
        
        # Sort by top-to-bottom
        blks.sort(key=lambda b: (b.bbox.top, b.bbox.x0))
        
        # Step 1: Cluster into lines
        lines = []
        current_line = [blks[0]]
        for b in blks[1:]:
            if abs(b.bbox.top - current_line[-1].bbox.top) < 8: # 8pt tolerance
                current_line.append(b)
            else:
                lines.append(current_line)
                current_line = [b]
        lines.append(current_line)

        # Step 2: Determine if this cluster is a table or paragraph
        table_keywords = ["total", "subtotal", "revenue", "rate", "balance", "amount", "qty", "paid", "due", "reimbursement", "hotel", "airfare", "auto", "parking"]
        
        def is_tabular_cluster(lines_list):
            if not lines_list: return False
            if len(lines_list) < 2: 
                # Single line with many items might be a table row
                return len(lines_list[0]) > 3
            
            # Check for multiple multi-cell lines
            multi_cell_lines = sum(1 for l in lines_list if len(l) > 2)
            if multi_cell_lines >= 2: return True
            
            # Check for high keyword density
            text_all = " ".join([" ".join([b.text for b in l]) for l in lines_list]).lower()
            if any(kw in text_all for kw in ["company paid", "employee paid", "total due"]): return True
            
            return False

        def is_kv_cluster(lines_list):
            if not lines_list: return False
            kv_count = 0
            for l in lines_list:
                text = " ".join([b.text for b in l])
                if ":" in text and len(text.split(":")[0]) < 30:
                    kv_count += 1
                elif len(l) == 2 and len(l[0].text) < 20: # Label Value adjacent
                    kv_count += 1
            return kv_count >= 1 # If even one line looks like KV in a small cluster

        if is_tabular_cluster(lines):
            # Construct TABLE block
            table_text = "\n".join([" ".join([b.text for b in l]) for l in lines])
            
            # Records & Markdown
            recovered_md = ""
            recovered_records = []
            for r_idx, r_line in enumerate(lines):
                r_line.sort(key=lambda b: b.bbox.x0)
                r_texts = [b.text for b in r_line]
                recovered_md += "| " + " | ".join(r_texts) + " |\n"
                if r_idx == 0 and len(lines) > 1: recovered_md += "| " + "--- | " * len(r_texts) + "\n"
                recovered_records.append({str(k): v for k, v in enumerate(r_texts)})

            # BBox
            x0 = min(b.bbox.x0 for b in blks); top = min(b.bbox.top for b in blks)
            x1 = max(b.bbox.x1 for b in blks); bot = max(b.bbox.bottom for b in blks)
            
            text_final = table_text[:400] + "... [Residual Table]" if len(table_text) > 400 else table_text
            
            roots.append(FullTextBlock(
                type=FullTextBlockType.TABLE,
                text=text_final.split('\n'),
                bbox=BoundingBox(x0=x0, top=top, x1=x1, bottom=bot, page_number=pn),
                page_number=pn,
                source_block_ids=[b.id for b in blks],
                source="mixed",
                confidence=sum(b.confidence for b in blks) / len(blks),
                structured_data={"markdown": recovered_md, "records": recovered_records},
                metadata={"label": "residual_table", "is_fallback": True}
            ))
        elif is_kv_cluster(lines):
             # Construct KEY_VALUE block
             kv_data = {}
             text_parts = []
             for l in lines:
                 l_text = " ".join([b.text for b in l])
                 text_parts.append(l_text)
                 if ":" in l_text:
                     parts = l_text.split(":", 1)
                     key = parts[0].strip()
                     val = parts[1].strip()
                     if key: kv_data[key] = val
                 elif len(l) == 2:
                     kv_data[l[0].text.strip(": ")] = l[1].text.strip()
             
             x0 = min(b.bbox.x0 for b in blks); top = min(b.bbox.top for b in blks)
             x1 = max(b.bbox.x1 for b in blks); bot = max(b.bbox.bottom for b in blks)
             
             roots.append(FullTextBlock(
                 type=FullTextBlockType.KEY_VALUE,
                 text="\n".join(text_parts),
                 bbox=BoundingBox(x0=x0, top=top, x1=x1, bottom=bot, page_number=pn),
                 page_number=pn,
                 source_block_ids=[b.id for b in blks],
                 source="mixed",
                 confidence=sum(b.confidence for b in blks) / len(blks),
                 structured_data={"pairs": kv_data},
                 metadata={"label": "residual_kv", "is_fallback": True}
             ))
        else:
            # Reconstruct as Paragraph
            text = " ".join([b.text for b in blks]).strip()
            x0 = min(b.bbox.x0 for b in blks); top = min(b.bbox.top for b in blks)
            x1 = max(b.bbox.x1 for b in blks); bot = max(b.bbox.bottom for b in blks)
            
            roots.append(FullTextBlock(
                type=FullTextBlockType.PARAGRAPH,
                text=text,
                bbox=BoundingBox(x0=x0, top=top, x1=x1, bottom=bot, page_number=pn),
                page_number=pn,
                source_block_ids=[b.id for b in blks],
                source="mixed",
                confidence=sum(b.confidence for b in blks) / len(blks),
                metadata={"label": "residual_text", "is_fallback": True}
            ))

    def _is_contained(self, inner: BoundingBox, outer: BoundingBox, padding: float = 15.0) -> bool:
        inner_cx = (inner.x0 + inner.x1) / 2.0
        inner_cy = (inner.top + inner.bottom) / 2.0
        return (outer.x0 - padding <= inner_cx <= outer.x1 + padding and 
                outer.top - padding <= inner_cy <= outer.bottom + padding)

    def _deduplicate_raw_blocks(self, blocks: List[RawBlock]) -> List[RawBlock]:
        """Merges or removes overlapping blocks with similar text to prevent 'ghosting'."""
        if not blocks: return []
        
        # Sort by page then spatial
        sorted_blks = sorted(blocks, key=lambda b: (b.bbox.page_number, b.bbox.top, b.bbox.x0))
        unique_blks = []
        skip_ids = set()

        for i, b1 in enumerate(sorted_blks):
            if b1.id in skip_ids: continue
            
            best_match = b1
            for j in range(i + 1, len(sorted_blks)):
                b2 = sorted_blks[j]
                if b2.bbox.page_number != b1.bbox.page_number: break
                if b2.bbox.top - b1.bbox.bottom > 20: break # Too far apart
                
                # Calculate IoU (Intersection over Union)
                inter_x0 = max(b1.bbox.x0, b2.bbox.x0)
                inter_top = max(b1.bbox.top, b2.bbox.top)
                inter_x1 = min(b1.bbox.x1, b2.bbox.x1)
                inter_bot = min(b1.bbox.bottom, b2.bbox.bottom)
                
                if inter_x1 > inter_x0 and inter_bot > inter_top:
                    inter_area = (inter_x1 - inter_x0) * (inter_bot - inter_top)
                    b1_area = (b1.bbox.x1 - b1.bbox.x0) * (b1.bbox.bottom - b1.bbox.top)
                    b2_area = (b2.bbox.x1 - b2.bbox.x0) * (b2.bbox.bottom - b2.bbox.top)
                    union_area = b1_area + b2_area - inter_area
                    iou = inter_area / union_area if union_area > 0 else 0
                    
                    # If IoU is high, check text similarity
                    if iou > 0.4: # Loosened IoU threshold
                        # Optimization: Skip expensive SequenceMatcher if lengths differ significantly
                        len_b1, len_b2 = len(b1.text), len(b2.text)
                        if len_b1 > 0 and len_b2 > 0:
                            max_len = max(len_b1, len_b2)
                            if abs(len_b1 - len_b2) / max_len > 0.4: # If >40% length diff, they can't match >0.7 sim
                                continue

                        sim = SequenceMatcher(None, b1.text, b2.text).ratio()
                        if sim > 0.7: # Loosened text similarity
                            # Prefer digital text over OCR, or higher confidence
                            if b2.source == "pdf_text" and b1.source != "pdf_text":
                                best_match = b2
                            elif b1.source == "pdf_text" and b2.source != "pdf_text":
                                best_match = b1
                            elif b2.confidence > b1.confidence:
                                best_match = b2
                            
                            skip_ids.add(b2.id)
                            logger.info(f"Deduplicated blocks: '{b1.text}' vs '{b2.text}' (IoU: {iou:.2f}, Sim: {sim:.2f})")
            
            unique_blks.append(best_match)
        
        if len(unique_blks) < len(blocks):
            logger.info(f"Deduplicated {len(blocks)} raw blocks down to {len(unique_blks)}")
        
        return unique_blks
