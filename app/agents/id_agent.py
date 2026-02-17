import ollama
import json

MODEL = "llama3.2:3b"


def extract_identity(page_text: str) -> dict:

    # Handle empty page
    if not page_text or not page_text.strip():
        return {
            "patient_name": None,
            "date_of_birth": None,
            "policy_number": None,
            "aadhaar_id": None
        }

    prompt = f"""You are a medical data extractor. Extract identity information from the document below.

FIELD MAPPING — look for these field names in the document:

patient_name  → look for: "Full Name", "Name", "Patient Name", "Payee", "Account Holder Name"
date_of_birth → look for: "Date of Birth", "DOB", "Birth Date", "D.O.B"
policy_number → look for: "Policy Number", "Policy No", "Insurance Number", "Policy ID"
aadhaar_id    → look for: "ID Number", "Aadhaar", "National ID", "Government ID", "Cheque Number", "Account Number"

RULES:
- Return STRICT JSON only. No explanation. No markdown. No code blocks.
- If a field is not found in the document, return null (not the string "null", actual null)
- Extract exactly what is written, do not guess or make up values

Return this exact format:
{{
  "patient_name": "value or null",
  "date_of_birth": "value or null",
  "policy_number": "value or null",
  "aadhaar_id": "value or null"
}}

Document:
{page_text}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    raw_output = response["message"]["content"].strip()

    # Strip markdown code fences if model adds them
    import re
    raw_output = re.sub(r"```(?:json)?", "", raw_output).strip()
    raw_output = raw_output.replace("```", "").strip()

    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        return {
            "patient_name": None,
            "date_of_birth": None,
            "policy_number": None,
            "aadhaar_id": None
        }

    # Enforce required keys
    required_keys = ["patient_name", "date_of_birth", "policy_number", "aadhaar_id"]
    for key in required_keys:
        if key not in data:
            data[key] = None

    # Clean up string "null" values — model sometimes returns "null" as a string
    for key in required_keys:
        if data[key] in ("null", "NULL", "Null", "none", "None", "N/A", "n/a", ""):
            data[key] = None

    return data