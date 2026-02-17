import ollama
import json
import re
from typing import List, Dict

MODEL = "llama3.2:3b"

DOCUMENT_TYPES = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other"
]

BATCH_SIZE = 5


def classify_batch(batch: List[Dict]) -> Dict[str, str]:

    pages_block = ""
    for page in batch:
        pages_block += f"\n--- PAGE {page['page_number']} ---\n{page['text'][:600]}\n"

    prompt = f"""You are a medical document classifier.

Classify each page into exactly one label.

LABELS:
claim_forms            → insurance claim forms, patient registration, consent forms,
                         appointment letters, referral letters, insurance verification,
                         medical history questionnaires, authorization forms

cheque_or_bank_details → bank cheque, account number, IFSC, SWIFT code, routing number,
                         any document with bank account details

identity_document      → government ID card, Aadhaar, PAN, passport, driving licence
                         — must have ID number + date of birth

itemized_bill          → hospital bill, pharmacy bill, invoice
                         — has list of items/services with individual prices and a TOTAL or SUBTOTAL
                         — look for words: BILL, INVOICE, ITEMIZED CHARGES, SUBTOTAL, TOTAL DUE, TOTAL AMOUNT

discharge_summary      → hospital discharge summary
                         — has Admission Date + Discharge Date + Diagnosis + Doctor name

prescription           → doctor prescription with Rx symbol
                         — has medication names with dosage and duration instructions

investigation_report   → lab report, blood test results, pathology report, radiology report
                         — has test names with RESULT and REFERENCE RANGE columns
                         — look for: CBC, metabolic panel, lipid panel, thyroid, blood count

cash_receipt           → simple payment receipt
                         — has Receipt Number + total AMOUNT PAID

other                  → anything that does not clearly match any category above

DECISION RULES — apply in this order:
1. Has test results with reference ranges → investigation_report
2. Has ID number + date of birth on an ID card → identity_document
3. Has bank account or cheque number → cheque_or_bank_details
4. Has ITEMIZED CHARGES or SUBTOTAL or TOTAL DUE with line items → itemized_bill
5. Has Rx + medication dosage + duration → prescription
6. Has Admission Date + Discharge Date → discharge_summary
7. Has Receipt Number + Amount Paid → cash_receipt
8. Everything else → claim_forms

Return ONLY a JSON object mapping page number to label.
No explanation. No markdown. No code blocks.

Example: {{"1": "claim_forms", "2": "identity_document", "3": "itemized_bill"}}

Pages:
{pages_block}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    raw = response["message"]["content"].strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    raw = raw.replace("```", "").strip()

    print(f"  Batch raw output: {raw}")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {str(p["page_number"]): "other" for p in batch}


def segregate_pages(pages: List[Dict]) -> Dict[str, List[str]]:

    # Normalize input
    normalized = []
    for page in pages:
        if isinstance(page, dict):
            normalized.append({
                "page_number": page.get("page_number", 0),
                "text": page["text"]
            })
        else:
            normalized.append({"page_number": 0, "text": page})

    # Classify in batches
    all_labels = {}
    for i in range(0, len(normalized), BATCH_SIZE):
        batch = normalized[i:i + BATCH_SIZE]
        print(f"  Classifying pages {batch[0]['page_number']} to {batch[-1]['page_number']}...")
        batch_labels = classify_batch(batch)
        all_labels.update(batch_labels)

    print("  Final labels:", all_labels)

    # Group texts by label
    grouped = {doc_type: [] for doc_type in DOCUMENT_TYPES}

    for page in normalized:
        page_num = str(page["page_number"])
        label = all_labels.get(page_num, "other").strip().lower()
        label = label.replace(" ", "_").replace("-", "_").strip(".,:")

        if label not in DOCUMENT_TYPES:
            label = "other"

        grouped[label].append(page["text"])

    return grouped