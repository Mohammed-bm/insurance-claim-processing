# 🏥 AI Claim Processing Pipeline

**An AI-powered system to automatically process medical claim PDFs using LangGraph and FastAPI.**  
Classifies claim documents, extracts structured medical and billing data, and returns validated JSON output using multi-agent orchestration.

---

## 🚀 Project Overview

This project is a **Proof of Work** demonstrating a scalable AI-driven document processing pipeline for medical insurance claims.

The system:

- Accepts a claim PDF
- Classifies pages into document types
- Routes pages to specialized AI extraction agents
- Extracts structured medical and billing data
- Returns a validated JSON response

Built with **FastAPI**, **LangGraph**, and **Ollama (local LLMs)**, the architecture emphasizes modularity, determinism, and production-readiness.

---

## 🎯 Key Features

- ✅ AI-powered document segregation (9 document types)
- ✅ Multi-agent extraction architecture
- ✅ Page-level routing (reduces cost & hallucination)
- ✅ Deterministic bill total calculation (no LLM math trust)
- ✅ Structured JSON validation with Pydantic
- ✅ Fail-safe agent design (partial success supported)
- ✅ Clean modular architecture for scalability

---

## 📚 Usage Flow

1. Client uploads claim PDF  
2. FastAPI receives `claim_id` + file  
3. PDF is split into page-level text  
4. **Segregator Agent** classifies each page  
5. Pages are routed to:
   - ID Agent  
   - Discharge Summary Agent  
   - Itemized Bill Agent  
6. Agents extract structured data  
7. Aggregator validates & merges results  
8. Final JSON response returned  

---

## 🏗️ Architecture Overview

This project follows a modular monolith architecture with clear separation of concerns.

### 🔹 1. FastAPI Layer
- Handles file upload
- Manages request lifecycle
- Triggers LangGraph workflow
- Returns structured JSON response

### 🔹 2. LangGraph Orchestration
- Controls node execution
- Enables conditional routing
- Maintains shared workflow state
- Designed for parallel agent execution (future-ready)

### 🔹 3. AI Agents

| Agent | Responsibility |
|--------|---------------|
| Segregator | Classifies pages into 9 document types |
| ID Agent | Extracts patient & policy information |
| Discharge Agent | Extracts hospitalization & diagnosis data |
| Bill Agent | Extracts billing line items |
| Aggregator | Validates & merges final output |

---

## 🔄 Workflow Diagram

```
START
  ↓
Segregator Agent
  ↓
Conditional Routing
  ├── ID Agent
  ├── Discharge Summary Agent
  ├── Itemized Bill Agent
  ↓
Aggregator
  ↓
END → JSON Response
```

---

## 🧠 Engineering Decisions

### ✔ Hybrid Segregation Strategy
- Rule-based keyword detection first
- LLM fallback for ambiguous pages
- Reduces cost and improves reliability

### ✔ Page-Level Routing
Agents only receive relevant pages — reducing:
- Token usage
- Hallucinations
- Latency

### ✔ Deterministic Financial Logic
All bill totals are calculated in Python.  
LLM outputs are never trusted for financial math.

### ✔ Strict Schema Enforcement
Pydantic models validate every extraction result to prevent malformed responses.

### ✔ Fail-Safe Architecture
Each agent:
- Handles internal exceptions
- Returns partial results if needed
- Prevents entire pipeline failure

---

## 🛠 Tech Stack

- FastAPI  
- LangGraph  
- Ollama (Local LLM)  
- Pydantic  
- Python 3.10+  

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/claim-processing.git
cd claim-processing
```

---

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Install Ollama

Download from:

https://ollama.com

Pull recommended model:

```bash
ollama pull llama3.1:8b
```

Or lightweight alternative:

```bash
ollama pull mistral:7b-instruct
```

---

### ▶ Run the Server

```bash
uvicorn app.main:app --reload
```

Server runs at:

```
http://127.0.0.1:8000
```

---

## 📡 API Usage

### Endpoint

```
POST /api/process
```

### Form Data

- `claim_id` (string)
- `file` (PDF)

### Example (curl)

```bash
curl -X POST "http://127.0.0.1:8000/api/process" \
  -F "claim_id=CLAIM123" \
  -F "file=@final.pdf"
```

---

## 📤 Sample Response

```json
{
  "claim_id": "CLAIM123",
  "identity_details": {},
  "discharge_summary": {},
  "itemized_bill": {
    "items": [],
    "calculated_total": 45870
  }
}
```

---

## 🔥 Key Engineering Challenges

- Structured extraction from inconsistent hospital PDFs  
- Numeric correctness in billing  
- LLM hallucination control  
- Token efficiency  
- Partial failure tolerance  

### Solutions Implemented

- Deterministic math validation  
- Schema enforcement  
- Hybrid classification  
- Temperature = 0 inference  
- Page-level routing strategy  

---

## 🚀 Future Improvements

- Async background job processing  
- Confidence scoring per agent  
- Human-in-the-loop review queue  
- Embedding-based document clustering  
- Model fallback strategy  

---

## 📜 License

MIT License © 2025

---

## 👤 Author

**Mohammed Ahmed**
