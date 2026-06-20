"""
Bionic reading conversion service for ClearSight Docs.
This service uses a page-by-page streaming design to avoid loading the full document
into memory at once. This ensures we adhere to the project's 'no OOM on large
academic documents' requirement from ARCHITECTURE.md while processing massive PDFs.
"""

import fitz
import re
import math
import html
import base64
import io
from typing import Callable
from collections import defaultdict


class BionicService:

    def convert_to_bionic_html(
        self, 
        pdf_path: str, 
        output_path: str, 
        bold_ratio: float = 0.5, 
        progress_callback: Callable[[int, int, str], None] | None = None
    ) -> dict:
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            if total_pages == 0:
                return {"success": False, "pages_processed": 0, "error_message": "Empty PDF"}

            # --- Pass 1: Size extraction for clustering ---
            size_pages: dict[float, set[int]] = defaultdict(set)
            all_block_sizes = []
            
            for page_num in range(1, total_pages + 1):
                page = doc[page_num - 1]
                blocks = page.get_text("dict").get("blocks", [])
                for block in blocks:
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        raw_spans = [s for s in line["spans"] if s["text"].strip()]
                        if raw_spans:
                            max_size = max(s["size"] for s in raw_spans)
                            size_key = round(max_size * 2) / 2
                            size_pages[size_key].add(page_num)
                            all_block_sizes.append(size_key)
                            
            body_text_sizes: set[float] = set()
            for size_key, pages in size_pages.items():
                if len(pages) > total_pages * 0.5:
                    body_text_sizes.add(size_key)
                    
            unique_heading_sizes = sorted(
                set(s for s in all_block_sizes if s not in body_text_sizes),
                reverse=True
            )
            
            clusters: list[float] = []
            for size in unique_heading_sizes:
                merged = False
                for c in clusters:
                    if abs(c - size) / max(c, size) < 0.10:
                        merged = True
                        break
                if not merged:
                    clusters.append(size)
                    
            top_clusters = clusters[:3]
            heading_size_to_level: dict[float, int] = {
                c: idx + 1 for idx, c in enumerate(top_clusters)
            }

            # --- Pass 2: Page-by-page streaming conversion ---
            pages_processed = 0
            partial_failure = False
            
            with open(output_path, "w", encoding="utf-8") as f_out:
                f_out.write("<!DOCTYPE html>\n")
                f_out.write('<html lang="en">\n<head>\n<meta charset="UTF-8">\n')
                f_out.write("<style>\n")
                f_out.write("body { max-width: 800px; margin: auto; line-height: 1.6; font-family: system-ui, sans-serif; padding: 2em; }\n")
                f_out.write("b { font-weight: 700; }\n")
                f_out.write("img { max-width: 100%; display: block; margin: 1em auto; }\n")
                f_out.write("h1, h2, h3 { margin-top: 1.5em; margin-bottom: 0.5em; }\n")
                f_out.write("</style>\n</head>\n<body>\n")
                
                for page_num in range(1, total_pages + 1):
                    if progress_callback:
                        progress_callback(page_num, total_pages, f"Converting page {page_num}")
                        
                    try:
                        page = doc[page_num - 1]
                        page_width = page.rect.width
                        blocks = page.get_text("dict").get("blocks", [])
                        
                        processed_blocks = []
                        
                        for block in blocks:
                            if "image" in block or block.get("type") == 1:
                                processed_blocks.append({
                                    "type": "image", 
                                    "bbox": block["bbox"]
                                })
                                continue
                                
                            if "lines" not in block:
                                continue
                                
                            lines_text = []
                            max_size_for_block = 0.0
                            
                            for line in block["lines"]:
                                raw_spans = [s for s in line["spans"] if s["text"].strip()]
                                if not raw_spans:
                                    continue
                            
                                combined_parts = []
                                for idx, s in enumerate(raw_spans):
                                    text = s["text"]
                                    if idx == 0:
                                        combined_parts.append(text)
                                        continue
                                    prev = raw_spans[idx - 1]
                                    prev_text = prev["text"]
                                    prev_size = prev["size"]
                                    curr_size = s["size"]
                            
                                    has_boundary_space = (
                                        (prev_text and prev_text[-1] == ' ')
                                        or (text and text[0] == ' ')
                                    )
                                    size_changes = abs(prev_size - curr_size) > 1.0
                                    prev_is_dropcap = len(prev_text.strip()) <= 3
                                    curr_starts_word = (
                                        text and text[0].isalpha()
                                        and prev_text and prev_text[-1].isalpha()
                                        and prev_text[-1].islower()
                                        and text[0].islower()
                                        and size_changes
                                        and not prev_is_dropcap
                                    )
                            
                                    if not has_boundary_space and size_changes and prev_is_dropcap:
                                        combined_parts.append(text)
                                    elif not has_boundary_space and curr_starts_word:
                                        combined_parts.append(' ')
                                        combined_parts.append(text)
                                    else:
                                        combined_parts.append(text)
                            
                                combined_text = "".join(combined_parts).strip()
                                combined_text = re.sub(r'  +', ' ', combined_text)
                                if not combined_text:
                                    continue
                                
                                lines_text.append(combined_text)
                                max_s = max(s["size"] for s in raw_spans)
                                if max_s > max_size_for_block:
                                    max_size_for_block = max_s

                            if not lines_text:
                                continue
                                
                            block_text = " ".join(lines_text)
                            block_size_key = round(max_size_for_block * 2) / 2
                            
                            block_type = "body"
                            level = 1
                            
                            is_body = False
                            for bts in body_text_sizes:
                                if bts > 0 and abs(bts - block_size_key) / max(bts, block_size_key) < 0.10:
                                    is_body = True
                                    break
                                    
                            if is_body:
                                block_type = "body"
                            else:
                                is_heading = False
                                for hs, lvl in heading_size_to_level.items():
                                    if hs > 0 and abs(hs - block_size_key) / max(hs, block_size_key) < 0.10:
                                        is_heading = True
                                        level = lvl
                                        break
                                if is_heading:
                                    block_type = "heading"
                                else:
                                    block_type = "body"
                                    
                            if block_type != "body" and len(lines_text) == 1:
                                if self._is_noise(lines_text[0]):
                                    block_type = "skip"
                                    
                            processed_blocks.append({
                                "type": block_type,
                                "level": level,
                                "text": block_text,
                                "bbox": block["bbox"]
                            })

                        processed_blocks = self._sort_blocks_multi_column(processed_blocks, page_width)
                        
                        for b in processed_blocks:
                            if b["type"] == "skip":
                                continue
                            elif b["type"] == "image":
                                try:
                                    pix = page.get_pixmap(clip=fitz.Rect(b["bbox"]), dpi=150)
                                    img_data = pix.tobytes("png")
                                    b64_img = base64.b64encode(img_data).decode('ascii')
                                    f_out.write(f'<img src="data:image/png;base64,{b64_img}">\n')
                                except Exception as img_e:
                                    print(f"Error extracting image on page {page_num}: {img_e}")
                            else:
                                bionic_text = self._bionic_tokenize(b["text"], bold_ratio)
                                if b["type"] == "heading":
                                    tag = f"h{b['level']}"
                                    f_out.write(f"<{tag}>{bionic_text}</{tag}>\n")
                                else:
                                    f_out.write(f"<p>{bionic_text}</p>\n")
                                    
                        pages_processed += 1
                        
                    except Exception as e:
                        print(f"Error processing page {page_num}: {e}")
                        partial_failure = True
                        continue
                        
                f_out.write("</body>\n</html>\n")
                
            return {
                "success": pages_processed > 0,
                "pages_processed": pages_processed,
                "error_message": "Partial failure occurred" if partial_failure else None
            }
            
        except Exception as e:
            print(f"convert_to_bionic_html error: {e}")
            return {"success": False, "pages_processed": 0, "error_message": str(e)}
        finally:
            if doc is not None:
                doc.close()

    def _is_noise(self, text: str) -> bool:
        if re.match(r'^\d+$', text): return True
        if len(text) <= 1: return True
        tokens = text.split()
        if len(tokens) >= 4 and all(len(t) <= 2 for t in tokens): return True
        if text and not text[0].isalnum() and text[0] not in ('"', "'"): return True
        if re.search(r'[=\#\}]', text): return True
        if re.match(r'^[A-Z]{1,4}\d{3,}', text) or re.match(r'^\d[A-Z]\d{3,}', text): return True
        if re.match(r'^[\-\–\—\(\)\+\=\/\\\.\,\d\s\#\}]+$', text): return True
        no_space = text.replace(' ', '')
        if (no_space == no_space.upper() and no_space.replace('-', '').isalpha() and len(no_space) <= 12): return True
        if len(text) <= 4 and not any(c.isalpha() for c in text): return True
        stripped = text.strip()
        if stripped.startswith('(') and stripped.endswith(')'):
            inner = stripped[1:-1].strip()
            if not inner or len(inner) <= 8 or not any(c.isalpha() for c in inner): return True
        if (text and text[0].islower() and re.search(r'[a-zA-Z][A-Z][a-z]', text)): return True
        return False

    def _sort_blocks_multi_column(self, blocks: list[dict], page_width: float) -> list[dict]:
        """
        Sort blocks in reading order, handling multi-column layouts correctly.
        Full-width blocks (>= 60% of page width) act as breakpoints that reset column flow.
        A single global (column_index, y) sort would incorrectly interleave content across
        these breaks (e.g., column 2 from above a heading would sort after column 1 from
        below the heading). Instead, we segment the page at every full-width block and
        only apply column-sorting within each segment.
        """
        if not blocks:
            return blocks

        # 1. Classify blocks
        for b in blocks:
            width = b["bbox"][2] - b["bbox"][0]
            b["is_wide"] = width >= 0.6 * page_width

        # 2. Compute column boundaries using ONLY narrow blocks
        narrow_blocks = [b for b in blocks if not b["is_wide"]]
        ranges = [(b["bbox"][0], b["bbox"][2]) for b in narrow_blocks]
        
        col_ranges = []
        if ranges:
            ranges.sort(key=lambda r: r[0])
            merged_ranges = [ranges[0]]
            for current in ranges[1:]:
                previous = merged_ranges[-1]
                if current[0] <= previous[1]:
                    merged_ranges[-1] = (previous[0], max(previous[1], current[1]))
                else:
                    merged_ranges.append(current)
            col_ranges = [r for r in merged_ranges if (r[1] - r[0]) > page_width * 0.15]

        # 3. Fallback: single column
        if len(col_ranges) < 2:
            blocks.sort(key=lambda b: b["bbox"][1])
            return blocks

        # 4. Segmented ordering
        # Sort all blocks top-to-bottom first
        blocks.sort(key=lambda b: b["bbox"][1])
        
        final_blocks = []
        current_segment = []

        def flush_segment():
            if not current_segment:
                return
            # Assign narrow blocks to columns
            for b in current_segment:
                center_x = (b["bbox"][0] + b["bbox"][2]) / 2
                assigned_col = 0
                for i, c in enumerate(col_ranges):
                    if c[0] <= center_x <= c[1]:
                        assigned_col = i
                        break
                b["col_idx"] = assigned_col
            # Sort segment by (col_idx, y0)
            current_segment.sort(key=lambda b: (b.get("col_idx", 0), b["bbox"][1]))
            final_blocks.extend(current_segment)
            current_segment.clear()

        for b in blocks:
            if b["is_wide"]:
                flush_segment()
                final_blocks.append(b)
            else:
                current_segment.append(b)
                
        flush_segment()
        
        return final_blocks

    def _bionic_tokenize(self, text: str, bold_ratio: float) -> str:
        tokens = text.split()
        out = []
        for token in tokens:
            if re.match(r'^\W*\d+\W*$', token):
                out.append(html.escape(token))
                continue
            if '=' in token or token.startswith('\\') or '^' in token or '_{' in token:
                out.append(html.escape(token))
                continue
                
            m = re.match(r'^(\W*)([a-zA-Z0-9_].*[a-zA-Z0-9_]|[a-zA-Z0-9_])(\W*)$', token)
            if m:
                prefix, core, suffix = m.groups()
                if any(c.isalpha() for c in core):
                    bold_len = math.ceil(len(core) * bold_ratio)
                    b_part = html.escape(core[:bold_len])
                    rest_part = html.escape(core[bold_len:])
                    new_token = f"{html.escape(prefix)}<b>{b_part}</b>{rest_part}{html.escape(suffix)}"
                    out.append(new_token)
                else:
                    out.append(html.escape(token))
            else:
                if any(c.isalpha() for c in token):
                    bold_len = math.ceil(len(token) * bold_ratio)
                    new_token = f"<b>{html.escape(token[:bold_len])}</b>{html.escape(token[bold_len:])}"
                    out.append(new_token)
                else:
                    out.append(html.escape(token))
        return " ".join(out)
