from typing import List
import statistics
from .domain import RawBlock, BoundingBox, BlockType

def reconstruct_rows(blocks: List[RawBlock]) -> List[RawBlock]:
    if not blocks:
        return []

    heights = [b.bbox.bottom - b.bbox.top for b in blocks]
    if not heights:
        return blocks
    
    median_height = statistics.median(heights)
    row_threshold = median_height * 0.7
    
    pages = {}
    for b in blocks:
        pn = b.bbox.page_number
        if pn not in pages:
            pages[pn] = []
        pages[pn].append(b)
        
    merged_blocks = []
    
    for pn in sorted(pages.keys()):
        page_blocks = sorted(pages[pn], key=lambda b: b.bbox.top)
        
        rows = []
        if page_blocks:
            current_row = [page_blocks[0]]
            
            def get_center_y(b):
                return (b.bbox.top + b.bbox.bottom) / 2.0
            
            row_sum_center_y = get_center_y(page_blocks[0])
            row_count = 1
            
            for b in page_blocks[1:]:
                b_center = get_center_y(b)
                avg_row_center = row_sum_center_y / row_count
                
                if abs(b_center - avg_row_center) < row_threshold:
                    current_row.append(b)
                    row_sum_center_y += b_center
                    row_count += 1
                else:
                    rows.append(current_row)
                    current_row = [b]
                    row_sum_center_y = b_center
                    row_count = 1
            rows.append(current_row)
            
        for i, row in enumerate(rows):
            row.sort(key=lambda b: b.bbox.x0)
            
            text_content = " ".join([b.text for b in row])
            
            x0 = min(b.bbox.x0 for b in row)
            top = min(b.bbox.top for b in row)
            x1 = max(b.bbox.x1 for b in row)
            bottom = max(b.bbox.bottom for b in row)
            
            merged_block = RawBlock(
                id=f"p{pn}_row{i}",
                text=text_content,
                bbox=BoundingBox(
                    x0=x0, top=top, x1=x1, bottom=bottom, page_number=pn
                ),
                block_type=BlockType.LINE,
                source=row[0].source 
            )
            merged_blocks.append(merged_block)
            
    return merged_blocks
