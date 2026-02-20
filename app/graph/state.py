from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class ClaimState(TypedDict):

    claim_id: str
    pages: List[Dict[str, Any]]

    identity_pages: List[str]
    discharge_pages: List[str]
    bill_pages: List[str]
    page_classification: Dict[str, int]

    identity_info: Optional[Dict[str, Any]]
    discharge_summary: Optional[Dict[str, Any]]
    itemized_bill: Optional[Dict[str, Any]]

    final_output: Optional[Dict[str, Any]]

    # 1. FLEXIBLE ADDITIONAL DOCUMENTS
    additional_documents: Optional[Dict[str, List[Dict[str, Any]]]]  
    # Stores prescriptions, investigation reports, cash receipts, etc.
    # Example: {"prescriptions": [{"medication": "Amoxicillin"}], "cash_receipts": [...]}
    
    # 2. METADATA & CONFIDENCE
    total_pages: int
    processing_time: Optional[float]
    confidence_scores: Optional[Dict[str, float]]  
    # Example: {"identity": 0.95, "discharge": 0.88, "bill": 0.92, "overall": 0.92}
    
    # 3. WARNINGS (Data Quality Issues)
    warnings: Optional[List[Dict[str, Any]]]  
    # Example: [{"code": "missing_signature", "message": "Form not signed", "page": 1}]
    
    # 4. FLEXIBLE FIELDS (Catch-all)
    raw_extractions: Optional[Dict[str, Any]]  
    # Raw data from each agent before processing
    
    unexpected_data: Optional[Dict[str, Any]]  
    # Anything that doesn't fit elsewhere