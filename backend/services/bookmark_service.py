"""
Bookmark service for ClearSight Docs.
Handles reading, modifying, and extracting PDF bookmarks (table of contents).
"""

import fitz
from pydantic import BaseModel
from typing import List
from pathlib import Path


class BookmarkNode(BaseModel):
    title: str
    page: int
    level: int
    children: List["BookmarkNode"] = []

BookmarkNode.model_rebuild()


class BookmarkService:

    def get_bookmarks(self, pdf_path: str) -> list[BookmarkNode]:
        doc = None
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()
            if not toc:
                return []
            return self._build_tree(toc)
        except Exception as e:
            print(f"Error getting bookmarks: {e}")
            raise
        finally:
            if doc is not None:
                doc.close()

    def write_bookmarks(self, pdf_path: str, bookmarks: list[BookmarkNode], output_path: str) -> None:
        if Path(pdf_path).resolve() == Path(output_path).resolve():
            raise ValueError("pdf_path and output_path cannot be the same file")
            
        flat_list = self._flatten_tree(bookmarks)
        
        doc = None
        try:
            doc = fitz.open(pdf_path)
            doc.set_toc(flat_list)
            doc.save(output_path)
        except Exception as e:
            print(f"Error writing bookmarks: {e}")
            raise
        finally:
            if doc is not None:
                doc.close()

    def _build_tree(self, flat_toc: list) -> list[BookmarkNode]:
        root = []
        stack = []  # List of (level, node)
        previous_level = 0
        
        for entry in flat_toc:
            raw_level, title, page = entry
            
            # Clamp forward jumps
            if raw_level > previous_level + 1:
                level = previous_level + 1
            else:
                level = raw_level
                
            node = BookmarkNode(title=title, page=page, level=level, children=[])
            
            if level == 1:
                root.append(node)
                stack = [(level, node)]
            elif level > previous_level:
                if stack:
                    stack[-1][1].children.append(node)
                else:
                    root.append(node)
                stack.append((level, node))
            else:
                while stack and stack[-1][0] >= level:
                    stack.pop()
                    
                if stack:
                    stack[-1][1].children.append(node)
                else:
                    root.append(node)
                stack.append((level, node))
                
            previous_level = level
            
        return root

    def _flatten_tree(self, nodes: list[BookmarkNode], result: list | None = None) -> list:
        if result is None:
            result = []
            
        for node in nodes:
            result.append([node.level, node.title, node.page])
            if node.children:
                self._flatten_tree(node.children, result)
                
        return result


    def extract_headings(self, pdf_path: str) -> tuple[list[BookmarkNode], bool]:
        import re
        from collections import defaultdict
        
        spans = []
        doc = None
        total_pages = 0
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            for page_index in range(total_pages):
                page = doc[page_index]
                blocks = page.get_text("dict").get("blocks", [])
                for block in blocks:
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            spans.append({
                                "text": span["text"].strip(),
                                "size": span["size"],
                                "flags": span["flags"],
                                "bbox": span["bbox"],
                                "page_num": page_index + 1
                            })
        finally:
            if doc is not None:
                doc.close()
                
        print(f"extract_headings: {len(spans)} total spans found")

        if len(spans) < 20:
            return ([], False)
            
        filtered_spans = []
        for span in spans:
            text = span["text"]
            if not text:
                continue
            # Skip purely numeric (page numbers, chapter numbers)
            if re.match(r'^\d+$', text):
                continue
            # Skip single characters (drop-caps, decorative letters)
            if len(text) <= 1:
                continue
            # Skip short ALL-CAPS fragments (decorative split words like "IRCUIT", "NALYSIS")
            if len(text) < 8 and text == text.upper() and text.isalpha():
                continue
            # Skip very small text
            if span["size"] < 8.0:
                continue
            # Skip cover page (page 1) — decorative title text, not content headings
            if span["page_num"] == 1:
                continue
            filtered_spans.append({
                "text": span["text"],
                "size": span["size"],
                "page_num": span["page_num"],
                "bbox_y": span.get("bbox", [0, 0, 0, 0])[1]
            })
            
        # Merge consecutive same-page same-size spans that are true line
        # continuations (bbox_y within 60px). Skips duplicate shadow renders
        # which share the same page and size but have nearly identical bbox_y.
        merged_spans = []
        i = 0
        while i < len(filtered_spans):
            current = filtered_spans[i]
            j = i + 1
            combined_text = current["text"]
            last_y = current.get("bbox_y", 0)
            while j < len(filtered_spans):
                nxt = filtered_spans[j]
                if nxt["page_num"] != current["page_num"]:
                    break
                if abs(nxt["size"] - current["size"]) / max(nxt["size"], current["size"]) >= 0.05:
                    break
                nxt_y = nxt.get("bbox_y", 0)
                delta_y = nxt_y - last_y
                # Must be a downward line continuation (10–60px gap)
                # Not a duplicate shadow (delta_y < 5) or unrelated block (> 60px)
                if not (5 < delta_y <= 60):
                    break
                if j - i >= 3:
                    break
                combined_text = combined_text.rstrip() + " " + nxt["text"].lstrip()
                last_y = nxt_y
                j += 1
            merged_spans.append({
                "text": combined_text.strip(),
                "size": current["size"],
                "page_num": current["page_num"],
                "bbox_y": current.get("bbox_y", 0)
            })
            i = j

        filtered_spans = merged_spans

        size_pages = defaultdict(set)
        for span in filtered_spans:
            size_pages[span["size"]].add(span["page_num"])
            
        body_text_sizes = set()
        for size, pages in size_pages.items():
            if len(pages) > total_pages * 0.6:
                body_text_sizes.add(size)
                
        print(f"extract_headings: body text sizes excluded: {body_text_sizes}")
        
        unique_sizes = set(span["size"] for span in filtered_spans if span["size"] not in body_text_sizes)
        sorted_sizes = sorted(unique_sizes, reverse=True)
        
        clusters = []
        for size in sorted_sizes:
            if not clusters:
                clusters.append(size)
            else:
                added = False
                for c_size in clusters:
                    if abs(c_size - size) / max(c_size, size) < 0.05:
                        added = True
                        break
                if not added:
                    clusters.append(size)
                    
        top_clusters = clusters[:3]
        
        heading_sizes_dict = {}
        for idx, c_size in enumerate(top_clusters):
            heading_sizes_dict[c_size] = idx + 1
            
        print(f"extract_headings: heading sizes selected: {heading_sizes_dict}")
        
        if not top_clusters:
            return ([], True)
            
        flat_list = []
        last_title = None
        last_page = None
        
        for span in filtered_spans:
            size = span["size"]
            level = None
            
            for c_size, lvl in heading_sizes_dict.items():
                if abs(c_size - size) / max(c_size, size) < 0.05:
                    level = lvl
                    break
                    
            if level is not None:
                if last_title == span["text"] and last_page == span["page_num"]:
                    continue
                flat_list.append([level, span["text"], span["page_num"]])
                last_title = span["text"]
                last_page = span["page_num"]
                
        print(f"extract_headings: {len(flat_list)} headings detected")
        
        tree = self._build_tree(flat_list)
        return (tree, True)

    def enrich_bookmarks(self, pdf_path: str) -> tuple[list[BookmarkNode], bool]:
        """
        If the PDF has an existing TOC, use its page numbers as anchors and
        replace generic labels (Chapter01, AppendixH, etc.) with titles
        detected from the actual page content.
        Falls back to extract_headings if no existing TOC.
        Returns (list[BookmarkNode], is_generated: bool)
        """
        import re

        doc = None
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()

            if not toc:
                doc.close()
                doc = None
                return self.extract_headings(pdf_path)

            # Build a map of page_num -> detected title by scanning only
            # the pages that are TOC anchor points
            anchor_pages = set(entry[2] for entry in toc)
            page_title_map: dict[int, str] = {}

            for page_num in anchor_pages:
                page_idx = page_num - 1
                if page_idx < 0 or page_idx >= len(doc):
                    continue
                page = doc[page_idx]
                spans = []
                for block in page.get_text("dict").get("blocks", []):
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            t = span["text"].strip()
                            if not t:
                                continue
                            if len(t) <= 1:
                                continue
                            if re.match(r'^\d+$', t):
                                continue
                            if len(t) < 8 and t == t.upper() and t.isalpha():
                                continue
                            if span["size"] < 10.0:
                                continue
                            if span["size"] > 60.0:
                                continue
                            # Skip page 1 entirely — cover page has decorative text only
                            if page_num == 1:
                                continue
                            spans.append({
                                "text": t,
                                "size": span["size"],
                                "bbox_y": span["bbox"][1]
                            })

                if not spans:
                    continue

                # Deduplicate spans with same text and nearly same bbox_y
                # (dual render passes produce identical spans ~2px apart)
                seen: list[dict] = []
                for s in spans:
                    is_dup = any(
                        s["text"] == x["text"] and abs(s["bbox_y"] - x["bbox_y"]) < 5
                        for x in seen
                    )
                    if not is_dup:
                        seen.append(s)
                spans = seen

                # Pick the largest font size on this page (excluding decorative > 60pt)
                candidate_spans = [s for s in spans if s["size"] <= 60.0]
                if not candidate_spans:
                    continue
                max_size = max(s["size"] for s in candidate_spans)

                # Collect all spans at the dominant heading size
                heading_spans = [
                    s for s in candidate_spans
                    if abs(s["size"] - max_size) / max_size < 0.05
                ]
                # Sort by vertical position
                heading_spans.sort(key=lambda s: s["bbox_y"])

                # Merge consecutive line-continuation spans (delta_y 5-60px)
                merged = []
                i = 0
                while i < len(heading_spans):
                    cur = heading_spans[i]
                    combined = cur["text"]
                    last_y = cur["bbox_y"]
                    j = i + 1
                    while j < len(heading_spans) and j - i < 3:
                        nxt = heading_spans[j]
                        delta_y = nxt["bbox_y"] - last_y
                        if not (5 < delta_y <= 60):
                            break
                        combined = combined.rstrip() + " " + nxt["text"].lstrip()
                        last_y = nxt["bbox_y"]
                        j += 1
                    merged.append(combined.strip())
                    i = j

                if merged:
                    page_title_map[page_num] = merged[0]

            # Build enriched TOC: replace generic labels where we found a title
            generic_pattern = re.compile(
                r'^(Chapter|Appendix|FrontMatter|Indx|Index|Formulacard|Appendix[A-Z_]+)\w*$',
                re.IGNORECASE
            )
            chapter_pattern = re.compile(r'[A-Za-z]+0*(\d+)$')
            enriched_toc = []
            for level, label, page in toc:
                detected = page_title_map.get(page)
                if detected and generic_pattern.match(label.replace(' ', '')):
                    chapter_match = chapter_pattern.match(label.replace(' ', ''))
                    if chapter_match:
                        num = chapter_match.group(1)
                        enriched_label = f"Chapter {num}: {detected}"
                    else:
                        enriched_label = detected
                    enriched_toc.append([level, enriched_label, page])
                else:
                    enriched_toc.append([level, label, page])

            tree = self._build_tree(enriched_toc)
            return (tree, True)

        except Exception as e:
            print(f"enrich_bookmarks error: {e}")
            raise
        finally:
            if doc is not None:
                doc.close()

_bookmark_service = BookmarkService()
