import ollama
import json
import re

MODEL = "llama3.2:3b"


def extract_single_bill(bill_text: str) -> dict:
    """Extract items from a single bill page"""
    
    if not bill_text or not bill_text.strip():
        return {
            "items": [],
            "declared_total": None,
            "calculated_total": 0,
            "total_matches": False
        }

    prompt = f"""
Extract all billed items and the total amount from this SINGLE bill.

CRITICAL RULES:
- Find the TOTAL AMOUNT printed on the bill (look for: TOTAL, TOTAL DUE, GRAND TOTAL, TOTAL AMOUNT, AMOUNT PAID)
- Extract that number EXACTLY as it appears
- DO NOT calculate it yourself
- DO NOT make up a number

Format:
{{
  "items": [
    {{"description": "...", "amount": number}}
  ],
  "declared_total": number
}}

If something is missing, return null.

Document:
{bill_text}
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    output = response["message"]["content"].strip()
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

    items = data.get("items") or []
    declared_total = data.get("declared_total")

    if declared_total is None:
        # Look for total patterns in the original text
        total_patterns = [
            r'TOTAL DUE:?\s*\$?([\d,]+\.?\d*)',
            r'TOTAL AMOUNT:?\s*\$?([\d,]+\.?\d*)',
            r'GRAND TOTAL:?\s*\$?([\d,]+\.?\d*)',
            r'AMOUNT PAID:?\s*\$?([\d,]+\.?\d*)',
            r'BALANCE DUE:?\s*\$?([\d,]+\.?\d*)',
            r'NET PAYABLE:?\s*\$?([\d,]+\.?\d*)',
            r'TOTAL[:\s]*\$?([\d,]+\.?\d*)',  # Generic total
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, bill_text, re.IGNORECASE)
            if match:
                total_str = match.group(1).replace(',', '')
                try:
                    declared_total = float(total_str)
                    print(f"  🔍 Found total with regex: {declared_total}")
                    break
                except ValueError:
                    continue

    calculated_total = sum(item.get("amount", 0) for item in items)
    total_matches = declared_total is not None and abs(calculated_total - declared_total) < 0.01

    return {
        "items": items,
        "declared_total": declared_total,
        "calculated_total": calculated_total,
        "total_matches": total_matches,
        "item_count": len(items),
        "difference": abs(calculated_total - declared_total) if declared_total else None
    }

def extract_bill(page_text: str) -> dict:
    """
    Main entry point - handles both single and multiple bills
    """
    
    if not page_text or not page_text.strip():
        return {
            "items": [],
            "declared_total": None,
            "calculated_total": 0,
            "total_matches": False,
            "bill_count": 0
        }
    
    # IMPROVED DETECTION: Check for multiple JSON objects or bill patterns
    # Count how many times bill indicators appear
    bill_indicators = [
        r'PHARMACY & OUTPATIENT BILL',
        r'BILLING DETAILS',
        r'INVOICE'
    ]
    
    # Count occurrences
    total_matches = 0
    for indicator in bill_indicators:
        matches = re.findall(indicator, page_text, re.IGNORECASE)
        total_matches += len(matches)
    
    # Also count JSON objects
    json_object_count = page_text.count('{')
    
    # If multiple indicators or multiple JSON objects, it's multiple bills
    if total_matches > 1 or json_object_count > 1:
        print("  📑 Multiple bills detected, processing separately...")
        
        # Try to split by common bill headers
        bill_sections = re.split(
            r'(?=PHARMACY & OUTPATIENT BILL|INVOICE|BILLING DETAILS|\{)', 
            page_text
        )
        
        # Filter out empty sections
        bill_sections = [s.strip() for s in bill_sections if s.strip() and len(s) > 50]
        
        print(f"    Found {len(bill_sections)} potential bill sections")
        
        all_items = []
        all_totals = []
        
        for i, section in enumerate(bill_sections):
            print(f"    Processing bill {i+1} of {len(bill_sections)}...")
            result = extract_single_bill(section)
            if result.get("items"):
                all_items.extend(result["items"])
                print(f"      Found {len(result['items'])} items")
            if result.get("declared_total"):
                all_totals.append(result["declared_total"])
        
        # Combine results
        combined = {
            "items": all_items,
            "declared_total": all_totals[0] if all_totals else None,
            "calculated_total": sum(item["amount"] for item in all_items),
            "total_matches": False,
            "item_count": len(all_items),
            "bill_count": len(bill_sections),
            "multiple_bills": True,
            "individual_totals": all_totals
        }
        
        print(f"  ✅ Combined {len(bill_sections)} bills with {len(all_items)} total items")
        return combined
    
    # Single bill
    print("  📄 Single bill detected")
    result = extract_single_bill(page_text)
    result["bill_count"] = 1
    result["multiple_bills"] = False
    return result