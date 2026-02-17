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