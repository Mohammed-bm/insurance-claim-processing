import pdfplumber
from typing import List, Dict
from io import BytesIO


def extract_pages(file_bytes: bytes) -> List[Dict]:
    pages = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""

            pages.append({
                "page_number": i,
                "text": text.strip()
            })

    return pages
