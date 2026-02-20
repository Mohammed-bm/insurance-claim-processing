from langgraph.graph import StateGraph, END
from datetime import datetime
from app.graph.state import ClaimState
from app.agents.segregator import segregate_pages
from app.agents.id_agent import extract_identity
from app.agents.discharge_agent import extract_discharge
from app.agents.bill_agent import extract_bill


def segregator_node(state: ClaimState) -> dict:
    print("\n[NODE] Segregator running...")

    pages = state["pages"]
    categorized, page_mapping = segregate_pages(pages)

    identity_pages  = categorized.get("identity_document", [])
    discharge_pages = categorized.get("discharge_summary", [])
    bill_pages      = categorized.get("itemized_bill", [])

    page_classification = page_mapping

    print(f"  Classification: {page_classification}")

    return {
        "identity_pages"     : identity_pages,
        "discharge_pages"    : discharge_pages,
        "bill_pages"         : bill_pages,
        "page_classification": page_classification,
    }


def id_agent_node(state: ClaimState) -> dict:
    print("\n[NODE] ID Agent running...")

    identity_pages = state.get("identity_pages", [])

    if not identity_pages:
        print("  No identity pages found, skipping.")
        return {"identity_info": None}

    combined_text = "\n\n".join(identity_pages)
    result = extract_identity(combined_text)
    print(f"  Extracted: {result}")
    return {"identity_info": result}


def discharge_agent_node(state: ClaimState) -> dict:
    print("\n[NODE] Discharge Agent running...")

    discharge_pages = state.get("discharge_pages", [])

    if not discharge_pages:
        print("  No discharge pages found, skipping.")
        return {"discharge_summary": None}

    combined_text = "\n\n".join(discharge_pages)
    result = extract_discharge(combined_text)
    print(f"  Extracted: {result}")
    return {"discharge_summary": result}


def bill_agent_node(state: ClaimState) -> dict:
    print("\n[NODE] Bill Agent running...")

    bill_pages = state.get("bill_pages", [])

    if not bill_pages:
        print("  No bill pages found, skipping.")
        return {"itemized_bill": None}

    combined_text = "\n\n".join(bill_pages)
    result = extract_bill(combined_text)
    print(f"  Extracted: {result}")
    return {"itemized_bill": result}


def aggregator_node(state: ClaimState) -> dict:
    print("\n[NODE] Aggregator running...")
    
    # Calculate confidence scores
    confidence_scores = state.get("confidence_scores", {})
    
    # If not already calculated, compute them
    if not confidence_scores:
        confidence_scores = {
            "identity": 0.9 if state.get("identity_info") and state["identity_info"].get("patient_name") else 0.0,
            "discharge": 0.9 if state.get("discharge_summary") and state["discharge_summary"].get("treating_doctor") else 0.0,
            "bill": 0.9 if state.get("itemized_bill") and state["itemized_bill"].get("items") else 0.0,
        }
        
        # Calculate overall
        scores = [v for v in confidence_scores.values() if v > 0]
        confidence_scores["overall"] = sum(scores) / len(scores) if scores else 0.0

    # Build comprehensive final output
    final_output = {
        # Core fields
        "claim_id": state.get("claim_id"),
        "processing_timestamp": datetime.utcnow().isoformat() + "Z",
        "processing_status": "completed",
        
        # Fixed core sections
        "identity_information": state.get("identity_info"),
        "discharge_summary": state.get("discharge_summary"),
        "itemized_bill": state.get("itemized_bill"),
        
        # Flexible additional documents (from state.py)
        "additional_documents": state.get("additional_documents", {}),
        
        # Page classification
        "page_classification": state.get("page_classification", {}),
        
        # Metadata
        "document_metadata": {
            "total_pages_processed": state.get("total_pages", 0),
            "processing_time_seconds": state.get("processing_time"),
            "confidence_scores": confidence_scores
        },
        
        # Warnings (from state.py)
        "warnings": state.get("warnings", []),
        
        # Flexible fields (from state.py)
        "flexible_fields": {
            "raw_extractions": state.get("raw_extractions", {}),
            "unexpected_data": state.get("unexpected_data", {})
        }
    }

    print("  Final output assembled with all fields.")
    
    # Also store in state
    state["final_output"] = final_output
    state["confidence_scores"] = confidence_scores
    
    return {"final_output": final_output}


def build_graph():
    graph = StateGraph(ClaimState)

    graph.add_node("segregator",      segregator_node)
    graph.add_node("id_agent",        id_agent_node)
    graph.add_node("discharge_agent", discharge_agent_node)
    graph.add_node("bill_agent",      bill_agent_node)
    graph.add_node("aggregator",      aggregator_node)

    graph.set_entry_point("segregator")

    graph.add_edge("segregator",      "id_agent")
    graph.add_edge("segregator",      "discharge_agent")
    graph.add_edge("segregator",      "bill_agent")

    graph.add_edge("id_agent",        "aggregator")
    graph.add_edge("discharge_agent", "aggregator")
    graph.add_edge("bill_agent",      "aggregator")

    graph.add_edge("aggregator",      END)

    return graph.compile()


claim_graph = build_graph()