# 📝 Changelog – Version 1.4 (November 2025 – July 2026)

This release introduces a fully autonomous LangGraph-based agent, end-to-end CAP subsidy application assistance, and significant improvements to the chat experience and developer tooling.

---

### 🚀 New Features & User Experience

* **Autonomous Agent Graph (LangGraph):** Replaced the initial Hermes Agent integration with a fully autonomous LangGraph-based agent. The new architecture features a deterministic intent router with confidence-gated classification, a clarify node for ambiguous inputs, secondary intent detection, and a modular node registry (`INTENT_REGISTRY`) for extensible routing.
* **CAP Application Workflow:** End-to-end CAP subsidy application assistance with slot tracking, form progress inspection (`cap_form_status` node), document inspection with PDF text extraction, interruption handling, and fast-path command routing for common CAP actions.
* **CAP Dataset Processing & Analysis:** Pipeline for processing 2023–2024 CAP datasets with parallel execution, PDF schema extraction, and eco-scheme classification data integration.
* **Enhanced Chat Capabilities:** Persistent `thread_id` per chat session, document and image upload support in the chat input, system command labels displayed in chat history, and improved input suggestion context handling.

---

### 🛠 Fixes & Stability Improvements

* **Input Suggestion Context:** Fixed the `/get-input-suggestion` endpoint to correctly pass `thread_id` from the frontend, ensuring suggestions are generated from the actual conversation history rather than an empty default session.
* **CAP Workflow State:** Unified CAP workflow state semantics, cleaned up dead code, and fixed `clear_cap_workflow` to perform a full state reset with confirmation.
* **Report Validation:** Bounded the report validation retry loop to a maximum of 2 attempts to prevent infinite loops.
* **Image Classification:** Fixed the `DESCRIBE_LONG_IMAGE` fast-path and widened the classifier context window for improved accuracy on large satellite images.
* **Rates Context:** Filtered rates context by language and deduplicated `RATES.md` logic to avoid redundant prompt content.
* **Metadata Lifecycle:** Fixed `thread_id` propagation in `/send-user-input` and resolved metadata lifecycle issues in the agent graph.

---

### ⚙️ Developer & Backend Enhancements

* **Agent Documentation:** Updated agent README and main README with the current graph topology, node registry, and routing logic.
* **Router Evaluation:** Added an offline router evaluation harness with a 25-case eval set for regression testing intent classification.
* **LLM Module Plan:** Added implementation plan documentation for the LLM module architecture.
* **Linting & Code Quality:** Resolved all Ruff linting and formatting issues across the codebase (89 check errors, 6 formatting files). Standardized on explicit `Optional` types, f-strings, and proper exception handling patterns.

---

# 📝 Changelog – Version 1.3 (September - November 2025)

This release unifies our codebase into a single repository and introduces major enhancements to our data processing, image super-resolution capabilities, and the core Eco-scheme classification engine.

---

### 🚀 New Features & User Experience

* **Custom SIGPAC Tools (Internal Rework):** The parcel drawing tool now uses our **newly developed and updated in-house SIGPAC tools** to automatically retrieve and process parcel metadata within Spanish territory. This update replaces previous reliance on external SIGPAC API packages, improving control and reliability.
* **Precision Eco-scheme Engine:** Implemented a new **server-side algorithm** designed for **high-precision Eco-scheme classification**. This engine correctly determines not only the *assignment* of Eco-schemes but also the **rate calculation precision** based on factors like irrigation and slope coefficients (Backend).
* **Enhanced Multilingual Support:** Enhanced language consistency and fixed various UI elements (e.g., Navbar) to ensure **proper English/Spanish language switching** across the application, especially for crop classification data (Frontend/Backend).
* **Improved Image Quality (SEN2SR):** Integrated the **SEN2SR Super-Resolution pipeline** to significantly improve the resolution and clarity of Sentinel-2 satellite imagery provided for parcel analysis (Backend).
* **Improved Chat Security:** Added **security against Markdown/HTML injection** in chat replies for a safer user experience (Frontend/Backend).

---

### 🛠 Fixes & Stability Improvements

* **Parcel Drawing Updates:** Parcel geometry updates are now properly reflected across the application after changes are made in the drawer (Frontend).
* **Image Pipeline Stability:** Implemented logic for **auto-retrying data retrieval** for cloudless images and resolved various CRS (Coordinate Reference System) and color correction issues for high-quality image processing (Backend).
* **General UI Fixes:** Fixed minor issues, including proper window height for tall images and general formatting bugs (Frontend).

---

### ⚙️ Developer & Backend Enhancements

* **Monorepo Migration:** **Successfully merged the Front-end and Back-end repositories** into this single repository. This simplifies development, tooling, and contribution for all future work.
* **Advanced Super-Resolution (SR) Benchmarking:** Introduced a comprehensive **VLM (Vision-Language Model) benchmarking pipeline**, which now includes an **SR Benchmark** to test the performance of the new **SEN2SR** integration against the project's previous iteration, **SuperRes4Sentinel (SR4S)** (Backend).
* **Modular Architecture:** Refactored core LLM and image processing functions into more modular components, improving code reuse and maintainability (Backend).
* **Automated PR Workflow:** Added a GitHub Action to **automatically append a bulleted list of commits** to the end of every Pull Request description, standardizing contribution transparency (General).