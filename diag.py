import fitz
import sys

doc = fitz.open("D:\\Boards\\ELECS\\EBOOKS\\Floyd - Electronic Devices.pdf")

with open("diag_out.txt", "w", encoding="utf-8") as f:
    for page_num in range(150, 250):  # rough guess for chap 4
        page = doc[page_num]
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                text = "".join(s["text"] for s in line["spans"])
                if "ipolar" in text or "Juncti" in text or "unction" in text:
                    f.write(f"--- Page {page_num+1} ---\n")
                    for s in line["spans"]:
                        if s["text"].strip() and s['size'] > 12:
                            f.write(f"Page {page_num+1} size={s['size']:.1f} text={repr(s['text'])}\n")
