
## 🧠 AgrIA Agentic Workflow Architecture

AgrIA uses a **LangGraph-driven stateful orchestration engine** that processes multi-modal agricultural queries, parcel visual metadata, and European Union / Spanish CAP (PAC) regulatory inquiries.

### 📐 Graph Topology Diagram

```mermaid
graph TD
    %% Node Definitions
    START([🚀 User Input / State Initialization])
    ROUTER{{"🧠 Router Node<br/>(Fast-Path & LLM Intent Classifier)"}}
    
    CONV["💬 Conversation Node<br/>(basic_chat)"]
    FALLBACK["🚫 Fallback Node<br/>(fallback_rejection)"]
    CAP["📜 CAP Regulatory Node<br/>(cap_query)"]
    RATES["💶 Ecoscheme Rates Node<br/>(ecoscheme_rates_node)"]
    REPORT["📊 Report Node<br/>(report_generator)"]
    VALIDATION["✅ Validation Node<br/>(report_validation)"]
    
    END([🏁 Final State Response / Output])

    %% Flow Connections
    START --> ROUTER

    %% Router Branching
    ROUTER -- "basic_chat" --> CONV
    ROUTER -- "fallback_rejection" --> FALLBACK
    ROUTER -- "cap_query" --> CAP
    ROUTER -- "ecoscheme_rates" --> RATES
    ROUTER -- "report_generator" --> REPORT

    %% Node Execution Outputs
    CONV --> END
    FALLBACK --> END
    CAP --> END
    RATES --> END

    %% Validation Loop Sub-Graph
    REPORT --> VALIDATION
    VALIDATION -- "Approved" --> END
    VALIDATION -- "Correction Required" --> REPORT

    %% Styling
    style START fill:#2d3748,stroke:#cbd5e0,color:#fff
    style END fill:#2d3748,stroke:#cbd5e0,color:#fff
    style ROUTER fill:#3182ce,stroke:#63b3ed,color:#fff
    style REPORT fill:#d69e2e,stroke:#f6e05e,color:#fff
    style VALIDATION fill:#d69e2e,stroke:#f6e05e,color:#fff
    style CAP fill:#38a169,stroke:#9ae6b4,color:#fff
    style RATES fill:#38a169,stroke:#9ae6b4,color:#fff
    style CONV fill:#805ad5,stroke:#d6bcfa,color:#fff
    style FALLBACK fill:#e53e3e,stroke:#feb2b2,color:#fff
```

## 🏛️ Architecture & Component Breakdown

### 1. State Management (`AgrIAState`)
The agent maintains an immutable execution state passed between nodes:
* `messages`: Full conversation thread (`List[BaseMessage]`).
* `lang`: Target response language (`"es"` | `"en"`).
* `crop_metadata`: SIGPAC / GIS parcel JSON payload (if provided).
* `visual_description`: Multi-modal VLM scene analysis.
* `correction_feedback`: Self-correction loop feedback for report generation.

---

### 2. Node Responsibilities

| Node Name | Module Path | Description / Scope |
| :--- | :--- | :--- |
| **Router** | `nodes/router_node.py` | Dual-mode intent classifier. Uses **Fast-Path** regex detection for rapid report triggers (`###DESCRIBE_SHORT_IMAGE###`) or a **Structured JSON LLM call** for natural language routing. |
| **Conversation** | `nodes/conversation_node.py` | Handles general domain chit-chat, greetings, and high-level non-regulatory agricultural questions. |
| **Fallback** | `nodes/fallback_node.py` | Out-of-scope filter. Politeness rejection for queries unrelated to agriculture, crops, or farming. |
| **CAP Query** | `nodes/cap_query.py` | Local RAG pipeline powered by **ChromaDB**. Retrieves semantically relevant legal contexts from regional/national PAC regulatory PDFs and `.md` files. |
| **Ecoscheme Rates** | `nodes/ecoscheme_rates_node.py` | Direct context injection node for Campaign Eco-scheme rates, financial thresholds, multi-annual premiums, and payment tables. |
| **Report** | `nodes/report_node.py` | Generates comprehensive parcel diagnostic reports combining SIGPAC metadata and VLM visual descriptions. |
| **Validation** | `nodes/validation_node.py` | Automated self-reflection node that evaluates generated reports against required schema metrics before returning output to the user. |

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