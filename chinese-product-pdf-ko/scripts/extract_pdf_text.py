import argparse
from pathlib import Path

import fitz


def main():
    parser = argparse.ArgumentParser(description="Extract per-page text from a PDF.")
    parser.add_argument("pdf", help="Input PDF path")
    parser.add_argument("--out", help="Optional UTF-8 text output path")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    doc = fitz.open(str(pdf_path))
    lines = [f"file: {pdf_path.name}", f"pages: {doc.page_count}", ""]
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        lines.append(f"--- page {index} chars {len(text)} ---")
        lines.append(text)
        lines.append("")

    output = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
