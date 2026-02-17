from app.agents.segregator import segregate_pages
from app.agents.id_agent import extract_identity
from app.agents.discharge_agent import extract_discharge
from app.agents.bill_agent import extract_bill


def process_claim(pages: list):

    # Step 1: Segregate
    categorized = segregate_pages(pages)

    result = {
        "identity": None,
        "discharge_summary": None,
        "bill": None
    }

    # Step 2: ID
    if categorized.get("identity_document"):
        page_text = categorized["identity_document"][0]
        result["identity"] = extract_identity(page_text)

    # Step 3: Discharge
    if categorized.get("discharge_summary"):
        page_text = categorized["discharge_summary"][0]
        result["discharge_summary"] = extract_discharge(page_text)

    # Step 4: Bill
    if categorized.get("itemized_bill"):
        page_text = categorized["itemized_bill"][0]
        result["bill"] = extract_bill(page_text)

    return result
