import ollama
import json
import re
from typing import List, Dict
from app.graph.state import ClaimState

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

BATCH_SIZE = 3

def is_bank_document(text: str) -> bool:
    """Quick pre-check for bank documents (no LLM needed)"""
    bank_keywords = [
        "CHEQUE", "CH-", "ACCOUNT NUMBER", "BANK NAME",
        "IFSC", "SWIFT", "ROUTING NUMBER", "BANK DETAILS",
        "Global Trust Bank", "Savings Account"
    ]
    
    text_upper = text.upper()
    matches = sum(1 for keyword in bank_keywords if keyword.upper() in text_upper)
    
    # If multiple bank keywords found, it's likely a bank document
    return matches >= 2

def classify_batch(batch: List[Dict], batch_start: int) -> Dict[str, str]:

    pages_block = ""
    actual_pages = []
    for i, page in enumerate(batch):
        absolute_num = batch_start + i
        actual_pages.append(absolute_num)
        # Show ONLY absolute page numbers - no confusing relative numbers
        pages_block += f"\n--- PAGE {absolute_num} ---\n{page['text'][:600]}\n"

    prompt = f"""You are a medical document classifier.

The page numbers shown below (PAGE {batch_start}, PAGE {batch_start+1}, etc.) are the ACTUAL page numbers in the document.
This batch contains pages: {[batch_start + i for i in range(len(batch))]}

Classify each page into exactly one label.

LABELS:
claim_forms            → insurance claim forms, patient registration, consent forms,
                         appointment letters, referral letters, insurance verification,
                         medical history questionnaires, authorization forms

cheque_or_bank_details → financial documents containing:
                         - Bank name (any bank name)
                         - Account number (typically 10-18 digits)
                         - Routing/IFSC code (alphanumeric code)
                         - SWIFT code (8 or 11 characters)
                         - Cheque number
                         Look for keywords: "BANK", "ACCOUNT", "CHEQUE", "IFSC", "SWIFT", "ROUTING NUMBER"

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
        return {str(batch_start + i): "other" for i, p in enumerate(batch)}  # ✅ Correct name

def segregate_pages(pages: List[Dict]) -> tuple:
    # Return both grouped texts AND page mapping
    normalized = []
    for idx, page in enumerate(pages):
        actual_page_num = idx + 1
        text = page["text"] if isinstance(page, dict) else page
        normalized.append({
            "page_number": actual_page_num,
            "text": text
        })
    
    # Classify
    all_labels = {}
    for i in range(0, len(normalized), BATCH_SIZE):
        batch = normalized[i:i + BATCH_SIZE]
        batch_start = i + 1
        batch_labels = classify_batch(batch, batch_start)
        all_labels.update(batch_labels)
    
    # Group by type AND track page numbers
    grouped = {doc_type: [] for doc_type in DOCUMENT_TYPES}
    page_mapping = {}  # ← NEW: Store page number -> document type
    
    for page in normalized:
        page_num = str(page["page_number"])
        label = all_labels.get(page_num, "other")
        grouped[label].append(page["text"])
        page_mapping[page_num] = label  # ← Store the mapping!
    
    return grouped, page_mapping  # ← Return both

# ===== ADD THIS NODE WRAPPER FUNCTION =====
def segregator_node(state: ClaimState) -> Dict:
    print("\n🔍 [SEGREGATOR NODE] Starting page classification...")
    
    pages = state.get("pages", [])
    
    # Get both grouped texts AND page mapping
    categorized, page_mapping = segregate_pages(pages)  # ← Now gets two things!
    
    # Extract the three core types
    identity_pages = categorized.get("identity_document", [])
    discharge_pages = categorized.get("discharge_summary", [])
    bill_pages = categorized.get("itemized_bill", [])
    
    # Store other document types
    additional_docs = {}
    for doc_type in ["prescription", "investigation_report", "cash_receipt", 
                     "claim_forms", "cheque_or_bank_details"]:
        if categorized.get(doc_type):
            additional_docs[doc_type] = categorized[doc_type]
    
    # Use the page_mapping instead of trying to match text!
    page_classification = page_mapping  # ← DIRECT mapping, no matching needed!
    
    # ... rest of your code ...
    
    return {
        "identity_pages": identity_pages,
        "discharge_pages": discharge_pages,
        "bill_pages": bill_pages,
        "additional_documents": additional_docs,
        "page_classification": page_classification,  # ← Now correct!
        "total_pages": len(pages),
        "warnings": warnings
    } 