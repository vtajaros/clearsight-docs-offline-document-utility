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

        # chapter_number_map: page_num -> digit string for large standalone digits
        # populated in Pass 1, used in Pass 6b
        chapter_number_map: dict[int, str] = {}

        doc = None
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            # ----------------------------------------------------------------
            # Pass 1: Line-level span assembly
            # Concatenate all spans within a fitz line to reconstruct words
            # split by drop-caps or ligature glyph substitution.
            # Use max_size (not dominant_size) for clustering — the largest
            # span on the line is the intended heading size.
            # ----------------------------------------------------------------
            lines: list[dict] = []

            for page_index in range(total_pages):
                page = doc[page_index]
                page_num = page_index + 1

                # Skip front cover (p1-2) and back cover (last 2 pages)
                if page_num <= 2 or page_num >= total_pages - 1:
                    continue

                # Detect embedded datasheet / figure pages:
                # if the majority of text on this page is very small (< 8pt),
                # it is a reproduced document image, not chapter content — skip it
                all_page_spans = [
                    s for block in page.get_text("dict").get("blocks", [])
                    if "lines" in block
                    for line in block["lines"]
                    for s in line["spans"]
                    if s["text"].strip()
                ]
                if all_page_spans:
                    tiny = sum(1 for s in all_page_spans if s["size"] < 8.0)
                    if tiny / len(all_page_spans) > 0.5:
                        continue  # skip this page — it's a datasheet/figure page

                for block in page.get_text("dict").get("blocks", []):
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        raw_spans = [s for s in line["spans"] if s["text"].strip()]
                        if not raw_spans:
                            continue

                        # Reconstruct line text with correct spacing.
                        # The PDF uses drop-cap rendering: large initial letter
                        # followed by smaller continuation spans, sometimes with
                        # no space between separate words (e.g. 'urrent' + 'in'
                        # -> "urrentin"). Fix: insert a space between spans when:
                        # - the previous span ends with a lowercase letter AND
                        #   the next span starts with a lowercase letter AND
                        #   neither span has a leading/trailing space
                        # - the next span is a known standalone short word
                        #   that has no leading space in the raw text
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

                            # Only insert a space when ALL of these are true:
                            # 1. No existing space at boundary
                            # 2. Font size CHANGES between spans (drop-cap -> body)
                            # 3. Previous span is a short drop-cap (<=3 chars after strip)
                            #    OR current span starts a new word (has leading space)
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
                                # Drop-cap initial followed by continuation —
                                # the continuation already belongs to the same word
                                # so no space needed (e.g. 'T' + 'he' = 'The')
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

                        max_size = max(s["size"] for s in raw_spans)

                        # Capture large standalone digit lines as chapter numbers
                        if re.match(r'^\d{1,2}$', combined_text) and max_size >= 40.0:
                            chapter_number_map[page_num] = combined_text
                            continue

                        lines.append({
                            "text": combined_text,
                            "max_size": max_size,
                            "dominant_size": max_size,
                            "page_num": page_num,
                            "bbox_y": line["bbox"][1],
                        })

        finally:
            if doc is not None:
                doc.close()

        # ----------------------------------------------------------------
        # Pass 1b: Merge section-number prefix lines with title lines
        # "1–1" at y=69.1 and "The Atom" at y=69.5 -> "1–1 The Atom"
        # Condition: same page, next line within 2px vertically,
        # current line matches section number pattern
        # ----------------------------------------------------------------
        section_num_pattern = re.compile(r'^\d{1,2}[–\-]\d{1,2}(?:\s|$)')
        merged_lines: list[dict] = []
        i = 0
        while i < len(lines):
            current = lines[i]
            # Check if this line is a standalone section number
            if (section_num_pattern.match(current["text"].strip())
                    and i + 1 < len(lines)):
                nxt = lines[i + 1]
                if (nxt["page_num"] == current["page_num"]
                        and abs(nxt["bbox_y"] - current["bbox_y"]) <= 2.0):
                    # Merge: prepend the section number to the title
                    merged_text = current["text"].strip() + " " + nxt["text"].strip()
                    merged_text = re.sub(r'  +', ' ', merged_text).strip()
                    merged_lines.append({
                        "text": merged_text,
                        "max_size": max(current["max_size"], nxt["max_size"]),
                        "dominant_size": max(current["dominant_size"], nxt["dominant_size"]),
                        "page_num": current["page_num"],
                        "bbox_y": current["bbox_y"],
                    })
                    i += 2
                    continue
            merged_lines.append(current)
            i += 1
        lines = merged_lines

        if len(lines) < 10:
            return ([], False)

        # ----------------------------------------------------------------
        # Pass 2: Filter noise lines
        # ----------------------------------------------------------------
        def is_noise(text: str) -> bool:
            # Pure digits
            if re.match(r'^\d+$', text):
                return True
            # Single character
            if len(text) <= 1:
                return True
            # Spaced-letter pattern: "H I S T O R Y  N O T E"
            tokens = text.split()
            if len(tokens) >= 4 and all(len(t) <= 2 for t in tokens):
                return True
            # Lines starting with non-alphanumeric (formula fragments: "}BASE", "–X", "=  –X")
            if text and not text[0].isalnum() and text[0] not in ('"', "'"):
                return True
            # Formula/equation patterns: contains = with surrounding math
            # Catches "C2R = –0.625 V", "VIN21###1", "= –X"
            if re.search(r'[=\#\}]', text):
                return True
            # Part number / component identifier patterns: "2N5484", "MMBF5484", "BC547"
            # Letter(s) + digits >= 3, or digits + letter(s) — datatable entries
            if re.match(r'^[A-Z]{1,4}\d{3,}', text) or re.match(r'^\d[A-Z]\d{3,}', text):
                return True
            # Symbol-only lines (math, formulas)
            if re.match(r'^[\-\–\—\(\)\+\=\/\\\.\,\d\s\#\}]+$', text):
                return True
            # All-caps short words: company logos, decorative headers, edition markers
            # "ANALOG", "DEVICES", "GLOBAL", "EDITION", "FEATURES", "HIGHLIGHTS"
            # Use len <= 12 to catch "HIGHLIGHTS" (10) and similar
            no_space = text.replace(' ', '')
            if (no_space == no_space.upper()
                    and no_space.replace('-', '').isalpha()
                    and len(no_space) <= 12):
                return True
            # Short with no letters
            if len(text) <= 4 and not any(c.isalpha() for c in text):
                return True
            # Parenthetical-only: "(FETs)", "( )", "(    )"
            stripped = text.strip()
            if stripped.startswith('(') and stripped.endswith(')'):
                inner = stripped[1:-1].strip()
                if not inner or len(inner) <= 8 or not any(c.isalpha() for c in inner):
                    return True
            # Garbled glyph encoding: line starts lowercase AND contains
            # mid-word uppercase — indicates corrupted PDF text layer
            # e.g. "nStrumentation amplifierS", "i Solation a mplifier S"
            # Exception: allow lines starting uppercase (normal title case)
            if (text and text[0].islower()
                    and re.search(r'[a-zA-Z][A-Z][a-z]', text)):
                return True
            return False

        filtered_lines = []
        for line in lines:
            text = line["text"]
            size = line["max_size"]  # Switched to max_size

            if is_noise(text):
                continue
            if size < 10.0:
                continue

            filtered_lines.append(line)

        if not filtered_lines:
            return ([], True)

        # ----------------------------------------------------------------
        # Pass 3: Fix concatenated words
        # ----------------------------------------------------------------
        def fix_concatenated_words(text: str) -> str:
            # "11–1The" -> "11–1 The", "15–6Active" -> "15–6 Active"
            # Digit immediately adjacent to a letter with no space
            fixed = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
            # "BipolarJunction" -> "Bipolar Junction"
            fixed = re.sub(r'([a-z])([A-Z])', r'\1 \2', fixed)
            # "FETAmplifiers" -> "FET Amplifiers"
            fixed = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1 \2', fixed)
            # Suffix split: ONLY apply when preceding segment is >= 5 chars
            # and suffix is a word that is never a word-ending in English.
            # "Introductionto" -> "Introduction to"  (10 chars before "to") OK
            # "Juntion" would need "on" but "Juncti" is 6 chars — excluded
            # because "on"/"or"/"in" are too common as word endings.
            # Safe suffixes: "and", "the", "for", "by", "of"
            fixed = re.sub(
                r'([a-z]{5,})(and|the|for|by|of)([A-Z])',
                r'\1 \2 \3', fixed
            )
            fixed = re.sub(
                r'([a-z]{5,})(and|the|for|by|of)$',
                r'\1 \2', fixed
            )
            # "Introductionto", "Answersto" — "to" only after >= 6 chars
            fixed = re.sub(
                r'([a-z]{6,})(to)([A-Z\s]|$)',
                lambda m: f'{m.group(1)} {m.group(2)}{m.group(3)}', fixed
            )
            return fixed

        for line in filtered_lines:
            line["text"] = fix_concatenated_words(line["text"])

        # ----------------------------------------------------------------
        # Pass 4: Body text exclusion (uses max_size now)
        # ----------------------------------------------------------------
        size_pages: dict = defaultdict(set)
        for line in filtered_lines:
            size_key = round(line["max_size"] * 2) / 2
            size_pages[size_key].add(line["page_num"])

        body_text_sizes: set = set()
        for size_key, pages in size_pages.items():
            if len(pages) > total_pages * 0.5:
                body_text_sizes.add(size_key)

        heading_lines = []
        for line in filtered_lines:
            size_key = round(line["max_size"] * 2) / 2
            if size_key not in body_text_sizes:
                heading_lines.append(line)

        if not heading_lines:
            return ([], True)

        # ----------------------------------------------------------------
        # Pass 5: Size clustering
        # ----------------------------------------------------------------
        unique_sizes = sorted(
            set(round(l["max_size"] * 2) / 2 for l in heading_lines),
            reverse=True
        )

        clusters: list[float] = []
        for size in unique_sizes:
            merged = False
            for i, c in enumerate(clusters):
                if abs(c - size) / max(c, size) < 0.10:
                    merged = True
                    break
            if not merged:
                clusters.append(size)

        top_clusters = clusters[:3]
        heading_size_to_level: dict[float, int] = {
            c: idx + 1 for idx, c in enumerate(top_clusters)
        }

        # ----------------------------------------------------------------
        # Pass 6: Multi-line title merging
        # ----------------------------------------------------------------
        merged_heading_lines: list[dict] = []
        i = 0
        while i < len(heading_lines):
            current = heading_lines[i]
            cur_size_key = round(current["max_size"] * 2) / 2

            if cur_size_key not in heading_size_to_level:
                merged_heading_lines.append(current)
                i += 1
                continue

            combined_text = current["text"]
            last_y = current["bbox_y"]
            j = i + 1

            while j < len(heading_lines) and (j - i) < 4:
                nxt = heading_lines[j]
                nxt_size_key = round(nxt["max_size"] * 2) / 2

                if nxt["page_num"] != current["page_num"]:
                    break
                if nxt_size_key != cur_size_key:
                    break

                delta_y = nxt["bbox_y"] - last_y
                if not (5 < delta_y <= 80):
                    break

                combined_text = combined_text.rstrip() + " " + nxt["text"].lstrip()
                last_y = nxt["bbox_y"]
                j += 1

            merged_heading_lines.append({
                "text": combined_text.strip(),
                "max_size": current["max_size"],
                "dominant_size": current["dominant_size"],
                "page_num": current["page_num"],
                "bbox_y": current["bbox_y"],
            })
            i = j

        # ----------------------------------------------------------------
        # Pass 6b: Associate chapter numbers
        # ----------------------------------------------------------------
        for line in merged_heading_lines:
            size_key = round(line["max_size"] * 2) / 2
            if size_key not in heading_size_to_level:
                continue
            if heading_size_to_level[size_key] != 1:
                continue
            page_num = line["page_num"]
            if page_num in chapter_number_map:
                num = chapter_number_map[page_num]
                if not line["text"].startswith(f"Chapter {num}"):
                    line["text"] = f"Chapter {num}: {line['text']}"

        # ----------------------------------------------------------------
        # Pass 7: Deduplicate and flatten
        # ----------------------------------------------------------------
        flat_list: list[list] = []
        seen: set[tuple] = set()

        for line in merged_heading_lines:
            size_key = round(line["max_size"] * 2) / 2
            level = None
            for c_size, lvl in heading_size_to_level.items():
                if abs(c_size - size_key) / max(c_size, size_key) < 0.10:
                    level = lvl
                    break
            if level is None:
                continue

            key = (line["text"], line["page_num"])
            if key in seen:
                continue
            seen.add(key)

            flat_list.append([level, line["text"], line["page_num"]])

        if not flat_list:
            return ([], True)

        def normalize_title(t: str) -> str:
            # Strip chapter prefix for comparison so "Chapter 14: X" vs "Chapter 14: Y"
            # compares only X vs Y
            t = re.sub(r'^chapter\s+\d+[:\s]+', '', t.strip().lower())
            # Remove all non-alphanumeric so glyph artifacts don't prevent matching:
            # "specialpurposeintegratedcircuits" == "specialpurposeintegratedcircuits"
            return re.sub(r'[^a-z0-9]', '', t)

        def has_glyph_artifact(text: str) -> bool:
            # Detects mid-word uppercase not at a word boundary:
            # "Special-purpoSe" -> 'o'+'S'+'e' matches [a-z][A-Z][a-z]
            # "Special-Purpose" -> 'e'+'-'+'P' does NOT match (hyphen breaks it)
            # "MMBF5484" -> all caps, no [a-z] before [A-Z], does NOT match
            return bool(re.search(r'[a-z][A-Z][a-z]', text))

        deduped: list[list] = []
        for entry in flat_list:
            level, title, page = entry
            norm = normalize_title(title)
            
            conflict_idx = None
            for idx, e in enumerate(deduped):
                if normalize_title(e[1]) == norm and abs(e[2] - page) <= 15:
                    conflict_idx = idx
                    break
                    
            if conflict_idx is None:
                deduped.append(entry)
            else:
                existing = deduped[conflict_idx]
                if has_glyph_artifact(existing[1]) and not has_glyph_artifact(title):
                    deduped[conflict_idx] = entry
                # else: keep existing (it was seen first and is not worse)
        flat_list = deduped

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
