import ollama
import json
import re

MODEL = "llama3.2:3b"


def extract_discharge(page_text: str):

    if not page_text or not page_text.strip():
        return {
            "diagnosis": None,
            "admission_date": None,
            "discharge_date": None,
            "treating_doctor": None
        }

    prompt = f"""You are a medical data extractor. Extract fields from this discharge summary.

FIELD MAPPING — look for these exact terms in the document:

diagnosis      → look for: "Admission Diagnosis", "Diagnosis", "Primary Diagnosis", "Presenting Diagnosis"
admission_date → look for: "Admission Date", "Date of Admission", "Admitted on", "Admitted Date"
discharge_date → look for: "Discharge Date", "Date of Discharge", "Discharged on"
treating_doctor → look for: "Attending Physician", "Treating Doctor", "Physician", "Digitally signed by", "Doctor"

RULES:
- Return STRICT JSON only. No explanation. No markdown. No code blocks.
- Copy the exact value from the document, do not paraphrase
- If a field is not found, return null

Return exactly this format:
{{
  "diagnosis": "value or null",
  "admission_date": "value or null",
  "discharge_date": "value or null",
  "treating_doctor": "value or null"
}}

Document:
{page_text}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    output = response["message"]["content"].strip()

    # Strip markdown fences
    output = re.sub(r"```(?:json)?", "", output).strip()
    output = output.replace("```", "").strip()

    print("RAW OUTPUT:")
    print(output)

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        print("JSON parsing failed.")
        return {
            "diagnosis": None,
            "admission_date": None,
            "discharge_date": None,
            "treating_doctor": None
        }

    # Enforce required keys and clean string nulls
    required_keys = ["diagnosis", "admission_date", "discharge_date", "treating_doctor"]
    for key in required_keys:
        if key not in data:
            data[key] = None
        if data[key] in ("null", "NULL", "Null", "none", "None", "N/A", "n/a", ""):
            data[key] = None

    return data