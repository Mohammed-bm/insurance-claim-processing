import ollama
import json
import re

MODEL = "llama3.2:3b"


def extract_bill(page_text: str):

    if not page_text or not page_text.strip():
        return {
            "items": [],
            "declared_total": None,
            "calculated_total": 0,
            "total_matches": False
        }

    prompt = f"""
Extract all billed items and the total amount.

Return JSON only. No explanation. No markdown. No code blocks.

Format:
{{
  "items": [
    {{"description": "...", "amount": number}}
  ],
  "declared_total": number
}}

If something is missing, return null.

Document:
{page_text}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    output = response["message"]["content"].strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    output = re.sub(r"```(?:json)?", "", output).strip()
    output = output.replace("```", "").strip()

    print("RAW OUTPUT:")
    print(output)

    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        print("JSON parsing failed.")
        return {
            "items": [],
            "declared_total": None,
            "calculated_total": 0,
            "total_matches": False
        }

    # Calculate and cross-check total
    items = data.get("items") or []
    declared_total = data.get("declared_total")

    calculated_total = sum(item.get("amount", 0) for item in items)

    total_matches = (
        declared_total is not None
        and calculated_total == declared_total
    )

    data["calculated_total"] = calculated_total
    data["total_matches"] = total_matches

    return data