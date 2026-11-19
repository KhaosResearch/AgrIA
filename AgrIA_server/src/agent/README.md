
## 🧠 AgrIA Agentic Workflow Architecture

AgrIA uses a **LangGraph-driven stateful orchestration engine** that processes multi-modal agricultural queries, parcel visual metadata, and European Union / Spanish CAP (PAC) regulatory inquiries.

### 📐 Graph Topology Diagram

```mermaid
graph LR
    %% Node Definitions
    START(["🚀 User Input / State Initialization"])
    ROUTER{{"🧠 State-Aware Router<br/>(Fast-paths + LLM Intent Classifier)"}}

    CONV["💬 Conversation Node<br/>(basic_chat)"]
    APP_USAGE["📖 App Usage Node<br/>(app_usage)"]
    FALLBACK["🚫 Fallback Node<br/>(fallback_rejection)"]
    CLARIFY["❓ Clarify Node<br/>(clarify)<br/>Low-confidence disambiguation"]

    CAP_INSPECT["🔍 CAP Document Inspector<br/>(cap_document_inspector_node)"]
    CAP_GUARD["🛡️ CAP Slot Guard<br/>(cap_slot_guard_node)<br/>Classifies intent + extracts slots"]
    CAP_INTERRUPT["🔀 CAP Interruption Handler<br/>(cap_interruption_node)<br/>Topic change / Pause / Resume"]
    CAP_APP["📋 CAP Application Node<br/>(cap_application_node)<br/>Merge slots + Validate + Collect"]
    CAP_STATUS["📝 CAP Form Status<br/>(cap_form_status_node)<br/>Read-only progress summary"]
    CAP["📜 CAP Regulatory Query<br/>(cap_query_node)"]

    RATES["💶 Ecoscheme Rates Node<br/>(ecoschemes_rates_node)"]
    REPORT["📊 Report Generator<br/>(report_node)"]
    VALIDATION["✅ Report Validation Node<br/>(validation_node)"]

    CLEAR_CAP["🧹 Clear CAP Workflow<br/>(clear_cap_workflow)"]

    END(["🏁 Output & State Persistence"])

    %% Entry Point
    START --> ROUTER

    %% Router Branching (10 intents from INTENT_REGISTRY)
    ROUTER -- "basic_chat" --> CONV
    ROUTER -- "app_usage" --> APP_USAGE
    ROUTER -- "fallback_rejection" --> FALLBACK
    ROUTER -- "cap_query" --> CAP
    ROUTER -- "ecoschemes_rates" --> RATES
    ROUTER -- "report_generator" --> REPORT
    ROUTER -- "cap_document_inspector" --> CAP_INSPECT
    ROUTER -- "cap_slot_guard" --> CAP_GUARD
    ROUTER -- "cap_application" --> CAP_APP
    ROUTER -- "cap_form_status" --> CAP_STATUS
    ROUTER -- "confidence < 0.55" --> CLARIFY

    %% CAP Document Inspection
    CAP_INSPECT -- "Extracted alignment / slots available" --> CAP_APP
    CAP_INSPECT -- "No alignment available" --> CAP

    %% CAP Slot Guard and Intent Routing
    CAP_GUARD -- "answer / correction / missing_information" --> CAP_APP
    CAP_GUARD -- "topic_change / pause / resume" --> CAP_INTERRUPT
    CAP_GUARD -- "cancel" --> CLEAR_CAP

    %% CAP Application Workflow
    CAP_APP -- "Missing or invalid required fields" --> END
    CAP_APP -- "Valid application / estimated amounts" --> END

    %% CAP Interruption Handling
    CAP_INTERRUPT -- "Unrelated question answered" --> END
    CAP_INTERRUPT -- "Pause: preserve form + pending_action" --> END
    CAP_INTERRUPT -- "Resume: re-enter application validation" --> CAP_APP

    %% Other Node Outputs
    CONV --> END
    APP_USAGE --> END
    FALLBACK --> END
    CLARIFY --> END
    CAP --> END
    RATES --> END
    CAP_STATUS --> END

    %% Report Validation Loop (max 2 retries)
    REPORT --> VALIDATION
    VALIDATION -- "Approved" --> END
    VALIDATION -- "Correction required (retry < 2)" --> REPORT
    VALIDATION -- "Max retries reached" --> END

    %% Workflow Clearing
    CLEAR_CAP --> END

    %% Styling
    style START fill:#2d3748,stroke:#cbd5e0,color:#fff
    style END fill:#2d3748,stroke:#cbd5e0,color:#fff
    style ROUTER fill:#3182ce,stroke:#63b3ed,color:#fff
    style CLARIFY fill:#d69e2e,stroke:#f6e05e,color:#fff
    style REPORT fill:#d69e2e,stroke:#f6e05e,color:#fff
    style VALIDATION fill:#d69e2e,stroke:#f6e05e,color:#fff
    style CAP_INSPECT fill:#319795,stroke:#81e6d9,color:#fff
    style CAP_GUARD fill:#2b6cb0,stroke:#90cdf4,color:#fff
    style CAP_INTERRUPT fill:#805ad5,stroke:#d6bcfa,color:#fff
    style CAP_APP fill:#38a169,stroke:#9ae6b4,color:#fff
    style CAP_STATUS fill:#38a169,stroke:#9ae6b4,color:#fff
    style CAP fill:#38a169,stroke:#9ae6b4,color:#fff
    style RATES fill:#38a169,stroke:#9ae6b4,color:#fff
    style CONV fill:#805ad5,stroke:#d6bcfa,color:#fff
    style APP_USAGE fill:#805ad5,stroke:#d6bcfa,color:#fff
    style FALLBACK fill:#e53e3e,stroke:#feb2b2,color:#fff
    style CLEAR_CAP fill:#718096,stroke:#cbd5e0,color:#fff
```

## 🏛️ Architecture & Component Breakdown

### 1. State Management (`AgrIAState`)
The agent maintains an immutable execution state passed between nodes:
* `messages`: Full conversation thread (`Annotated[list[BaseMessage], add_messages]`).
* `lang`: Target response language (`"es"` | `"en"`).
* `crop_metadata`: SIGPAC / GIS parcel JSON payload (if provided). Persists across report generations.
* `cap_form_data`: CAP slots collected across conversation turns, keyed by field name.
* `assessment_report`: Raw parcel assessment markdown string. Cleared when a new parcel is loaded.
* `pending_action`: Active interaction flow marker (e.g., `"AWAITING_SLOT:surface_ha"`).
* `cap_workflow`: Current stage in the CAP workflow (`"collect"` | `"assess"` | `"ready"` | `"paused"` | `"cancelled"` | `"unrelated"`).
* `cap_alignment`: Slot guard verdict for the latest user turn.
* `cap_rates`: Explicit EUR/ha rate table used to reproduce financial amounts.
* `visual_description`: Multi-modal VLM scene analysis.
* `correction_feedback`: Self-correction loop feedback for report generation.
* `report_retry_count`: Number of validation retries for the current report (max 2).
* `secondary_intent`: Secondary intent detected by the router (e.g., a user asking about rates *and* how to fill the form). Consumed by advisory nodes to address both concerns in one response.

**Intent Registry** (`INTENT_REGISTRY` in `state_models.py`): Single source of truth for the 10 valid router intents. The graph's `ROUTER_TARGETS`, the LLM classifier prompt, and the eval harness all derive from this set — adding a new intent requires one entry here plus a node and prompt.

---

### 2. Node Responsibilities

| Node Name | Module Path | Description / Scope |
| :--- | :--- | :--- |
| **Router** | `nodes/router_node.py` | Hybrid intent router. **Fast-paths** (zero LLM cost): `pending_action` slot continuation, `###DESCRIBE_*_IMAGE###` report triggers, empty messages. **LLM classifier**: structured JSON call with `INTENT.md` prompt (10 intents + `secondary_intent` + `confidence`). Routes to `clarify` when confidence < 0.55. Every decision is logged via `_log_routing()`. |
| **Basic Chat** | `nodes/basic_chat_node.py` | Handles general domain chit-chat, greetings, and high-level non-regulatory agricultural questions. |
| **App Usage** | `nodes/app_usage_node.py` | Helps with general use-of-the-tool questions and guides the user with step-by-step replies on how to engage properly with the app. |
| **Fallback** | `nodes/fallback_node.py` | Out-of-scope filter. Politeness rejection for queries unrelated to agriculture, crops, or farming. |
| **Clarify** | `nodes/router_node.py` | Deterministic (no LLM) disambiguation node. When the classifier's confidence is below threshold, asks one targeted question with multiple-choice options instead of guessing. |
| **CAP Document Inspector** | `nodes/cap_document_inspector_node.py` | Analyzes uploaded CAP application forms (PDF) to extract parcel alignment, slot details, and form attributes. Reuses `CAP_SLOT_GUARD.md` as system prompt. |
| **CAP Slot Guard** | `nodes/cap_slot_guard_node.py` | Classifies user intent within the CAP application flow (`answer`, `correction`, `pause`, `cancel`, `resume`, `topic_change`) and extracts slot values. 2 LLM attempts + deterministic fallback gated by schema. |
| **CAP Interruption Handler** | `nodes/cap_interruption_node.py` | Manages active application flow interruptions: topic changes (delegates to `basic_chat`, preserves form state), pausing, and resuming. |
| **CAP Application** | `nodes/cap_application_node.py` | Merges collected slots (schema-gated), validates required fields, asks exactly one next question, or - when valid - computes estimated CAP aid amounts from `CAP_RATES.json` and narrates the pre-calculated figures. |
| **CAP Form Status** | `nodes/cap_form_status_node.py` | Deterministic (no LLM) read-only node. Returns a structured summary of the current form: collected fields, pending field, workflow state. Does not mutate state. |
| **CAP Query** | `nodes/cap_query_node.py` | Local RAG pipeline powered by **ChromaDB**. Retrieves semantically relevant legal contexts from regional/national PAC regulatory PDFs and `.md` files. Preserves `pending_action` (does not abandon the form). |
| **Ecoscheme Rates** | `nodes/ecoscheme_rates_node.py` | Injects the language-relevant block from `classification.json` (ES or EN only, ~5.5 KB) for eco-scheme rates, financial thresholds, and payment tables. |
| **Report** | `nodes/report_node.py` | Generates comprehensive parcel diagnostic reports combining SIGPAC metadata and VLM visual descriptions. |
| **Validation** | `nodes/validation_node.py` | Deterministic (no LLM) report validator. Checks for markdown table presence and total area consistency. Bounded retry loop (max 2 attempts) before returning the last attempt. |
| **Clear CAP Workflow** | `nodes/router_node.py` | Utility node to reset `pending_action`, `cap_workflow`, and `cap_alignment`. Reached from the slot guard's `cancel` verdict. |
---

### 3. Vector Database & RAG Stack
* **Storage Engine**: Embedded ChromaDB (`VECTOR_DB_PATH`).
* **Embeddings**: Local ONNX / standard sentence-transformers (`all-MiniLM-L6-v2`).
* **Retrieval Mode**: Top-$k$ similarity search with metadata-preserved Markdown chunking (`RecursiveCharacterTextSplitter`).
 
---

## 🧪 Testing

Run the full automated pytest suite covering all graph execution paths:

```bash
cd AgrIA_server
uv run pytest test/ -vv
```

### Router Evaluation Harness

A dedicated eval harness (`test/agent/test_router_eval.py`) measures the intent classifier's routing precision against a labeled eval set (`router_eval_set.json`, 27 cases covering fast-paths, all 10 intents, multi-intent, and ambiguous messages):

```bash
# Offline mode (keyword-based classifier emulation, no API key needed)
uv run pytest test/agent/test_router_eval.py -v

# Live mode (real LLM classifier, requires LLM_API_KEY)
uv run pytest test/agent/test_router_eval.py -v --live
```