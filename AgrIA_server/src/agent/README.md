
## 🧠 AgrIA Agentic Workflow Architecture

AgrIA uses a **LangGraph-driven stateful orchestration engine** that processes multi-modal agricultural queries, parcel visual metadata, and European Union / Spanish CAP (PAC) regulatory inquiries.

### 📐 Graph Topology Diagram

```mermaid
graph LR
    %% Node Definitions
    START(["🚀 User Input / State Initialization"])
    ROUTER{{"🧠 State-Aware Router<br/>(Reads Msg + AgrIAState Flags)"}}

    CONV["💬 Conversation Node<br/>(basic_chat)"]
    APP_USAGE["📖 App Usage Node<br/>(app_usage)"]
    FALLBACK["🚫 Fallback Node<br/>(fallback_rejection)"]

    CAP_INSPECT["🔍 CAP Document Inspector<br/>(cap_document_inspector_node)"]
    CAP_GUARD["🛡️ CAP Slot Guard<br/>(cap_slot_guard_node)<br/>Classifies intent + extracts slots"]
    CAP_INTERRUPT["🔀 CAP Interruption Handler<br/>(cap_interruption_node)<br/>Topic change / Pause / Cancel / Resume"]
    CAP_APP["📋 CAP Application Node<br/>(cap_application_node)<br/>Merge slots + Validate + Collect"]
    CAP["📜 CAP Regulatory Query<br/>(cap_query_node)"]

    RATES["💶 Ecoscheme Rates Node<br/>(ecoschemes_rates_node)"]
    REPORT["📊 Report Generator<br/>(generate_report_node)"]
    VALIDATION["✅ Report Validation Node<br/>(validate_report_node)"]

    CLEAR_CAP["🧹 Clear CAP Workflow<br/>(clear_cap_workflow)"]

    END(["🏁 Output & State Persistence"])

    %% Entry Point
    START --> ROUTER

    %% Router Branching
    ROUTER -- "basic_chat" --> CONV
    ROUTER -- "app_usage" --> APP_USAGE
    ROUTER -- "fallback_rejection" --> FALLBACK
    ROUTER -- "cap_query" --> CAP
    ROUTER -- "ecoschemes_rates" --> RATES
    ROUTER -- "report_generator" --> REPORT
    ROUTER -- "cap_document_inspector" --> CAP_INSPECT
    ROUTER -- "cap_slot_guard" --> CAP_GUARD
    ROUTER -- "cap_application" --> CAP_APP

    %% CAP Document Inspection
    CAP_INSPECT -- "Extracted alignment / slots available" --> CAP_APP
    CAP_INSPECT -- "No alignment available" --> CAP

    %% CAP Slot Guard and Intent Routing
    CAP_GUARD -- "answer / correction / missing_information" --> CAP_APP
    CAP_GUARD -- "topic_change / pause / cancel / resume" --> CAP_INTERRUPT

    %% CAP Application Workflow
    CAP_APP -- "Missing or invalid required fields" --> END
    CAP_APP -- "Valid application / estimated amounts" --> END

    %% CAP Interruption Handling
    CAP_INTERRUPT -- "Unrelated question answered" --> END
    CAP_INTERRUPT -- "Pause: preserve form + pending_action" --> END
    CAP_INTERRUPT -- "Cancel: clear active form + pending_action" --> END
    CAP_INTERRUPT -- "Resume: re-enter application validation" --> CAP_APP

    %% Other Node Outputs
    CONV --> END
    APP_USAGE --> END
    FALLBACK --> END
    CAP --> END
    RATES --> END

    %% Report Validation Loop
    REPORT --> VALIDATION
    VALIDATION -- "Approved" --> END
    VALIDATION -- "Correction required" --> REPORT

    %% Workflow Clearing
    CLEAR_CAP --> END

    %% Styling
    style START fill:#2d3748,stroke:#cbd5e0,color:#fff
    style END fill:#2d3748,stroke:#cbd5e0,color:#fff
    style ROUTER fill:#3182ce,stroke:#63b3ed,color:#fff
    style REPORT fill:#d69e2e,stroke:#f6e05e,color:#fff
    style VALIDATION fill:#d69e2e,stroke:#f6e05e,color:#fff
    style CAP_INSPECT fill:#319795,stroke:#81e6d9,color:#fff
    style CAP_GUARD fill:#2b6cb0,stroke:#90cdf4,color:#fff
    style CAP_INTERRUPT fill:#805ad5,stroke:#d6bcfa,color:#fff
    style CAP_APP fill:#38a169,stroke:#9ae6b4,color:#fff
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
* `crop_metadata`: SIGPAC / GIS parcel JSON payload (if provided).
* `cap_form_data`: CAP slots collected across conversation turns, keyed by field name.
* `assessment_report`: Raw parcel assessment markdown string.
* `pending_action`: Active interaction flow marker (e.g., `"AWAITING_CAP_DOC"`, `"AWAITING_SLOT:surface_ha"`).
* `cap_workflow`: Current stage in the CAP workflow (`"collect"` | `"assess"` | `"ready"` | `"unrelated"`).
* `cap_alignment`: Slot guard verdict for the latest user turn.
* `cap_rates`: Explicit EUR/ha rate table used to reproduce financial amounts.
* `visual_description`: Multi-modal VLM scene analysis.
* `correction_feedback`: Self-correction loop feedback for report generation.

---

### 2. Node Responsibilities

| Node Name | Module Path | Description / Scope |
| :--- | :--- | :--- |
| **Router** | `nodes/router_node.py` | Dual-mode intent classifier. Uses **Fast-Path** regex detection for rapid report triggers (`###DESCRIBE_SHORT_IMAGE###`) or a **Structured JSON LLM call** for natural language routing. |
| **Basic Chat** | `nodes/basic_chat_node.py` | Handles general domain chit-chat, greetings, and high-level non-regulatory agricultural questions. |
| **App Usage** | `nodes/app_usage_node.py` | Helps with general use-of-the-tool questions and guides the user with step-by-step replies on how to engage properly with the app. |
| **Fallback** | `nodes/fallback_node.py` | Out-of-scope filter. Politeness rejection for queries unrelated to agriculture, crops, or farming. |
| **CAP Document Inspector** | `nodes/cap_document_inspector_node.py` | Analyzes uploaded user-uploaded CAP application forms to extract parcel alignment, slot details, and form attributes. |
| **CAP Slot Guard** | `nodes/cap_slot_guard_node.py` | Classifies user intent within the CAP application flow and extracts slot values for form completion. |
| **CAP Interruption Handler** | `nodes/cap_interruption_node.py` | Manages active application flow interruptions including topic changes, pausing, canceling, or resuming forms. |
| **CAP Application** | `nodes/cap_application_node.py` | Merges collected slots, validates required fields, and computes estimated CAP aid amounts. |
| **CAP Query** | `nodes/cap_query_node.py` | Local RAG pipeline powered by **ChromaDB**. Retrieves semantically relevant legal contexts from regional/national PAC regulatory PDFs and `.md` files. |
| **Ecoscheme Rates** | `nodes/ecoschemes_rates_node.py` | Direct context injection node for Campaign Eco-scheme rates, financial thresholds, multi-annual premiums, and payment tables. |
| **Report** | `nodes/report_node.py` | Generates comprehensive parcel diagnostic reports combining SIGPAC metadata and VLM visual descriptions. |
| **Validation** | `nodes/validation_node.py` | Automated self-reflection node that evaluates generated reports against required schema metrics before returning output to the user. |
| **Clear CAP Workflow** | `nodes/clear_cap_workflow_node.py` | Utility node to reset and clean active CAP application state flags and pending actions. |

---

### 3. Vector Database & RAG Stack
* **Storage Engine**: Embedded ChromaDB (`VECTOR_DB_PATH`).
* **Embeddings**: Local ONNX / standard sentence-transformers (`all-MiniLM-L6-v2`).
* **Retrieval Mode**: Top-$k$ similarity search with metadata-preserved Markdown chunking (`RecursiveCharacterTextSplitter`).
 
---

## 🧪 Testing

Run the full automated pytest suite covering all graph execution paths (Tests A through E):

```bash
cd AgrIA_server
uv run pytest test/ -vv
```