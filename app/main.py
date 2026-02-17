from fastapi import FastAPI, UploadFile, File, Form
from datetime import datetime

from app.services.pdf_loader import extract_pages
from app.graph.workflow import claim_graph

app = FastAPI(title="Claim Processing API")


@app.post("/api/process")
async def process_claim(
    claim_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Step 1: Read uploaded PDF
    file_bytes = await file.read()

    # Step 2: Extract pages
    pages = extract_pages(file_bytes)
    print(f"\nClaim {claim_id}: {len(pages)} pages extracted from {file.filename}")

    # Step 3: Build initial state
    initial_state = {
        "claim_id"           : claim_id,
        "pages"              : pages,
        "identity_pages"     : [],
        "discharge_pages"    : [],
        "bill_pages"         : [],
        "page_classification": {},
        "identity_info"      : None,
        "discharge_summary"  : None,
        "itemized_bill"      : None,
        "final_output"       : None,
    }

    # Step 4: Run the LangGraph pipeline
    final_state = claim_graph.invoke(initial_state)

    # Step 5: Return response
    return {
        "claim_id"   : claim_id,
        "status"     : "processed",
        "timestamp"  : datetime.utcnow().isoformat() + "Z",
        "total_pages": len(pages),
        **final_state["final_output"]
    }