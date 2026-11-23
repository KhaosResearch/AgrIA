# Implementation Plan — AgrIA LLM Module: Current State & Decision-Level Refactor Options

[Overview]
This document is a **state-of-the-art summary and decision-level analysis** of the LLM module in AgrIA. It is NOT a commitment to a concrete architecture. It covers: (1) what the current LangGraph-based integration does, (2) what it does well, (3) what breaks or is under-covered as usage grows, and (4) the decision-space for refactoring the *decision layer* (routing, workflow control, guardrails) — with tradeoffs — so a concrete architecture can be chosen afterwards.

Scope: `AgrIA_server/src/agent/`, `AgrIA_server/src/services/chat_service.py`, `AgrIA_server/src/endpoints/chat.py`, `AgrIA_server/src/utils/{nodes_utils,cap_form_utils,rag_utils,chat_utils}.py`, `AgrIA_server/src/models/state_models.py`, and all assets under `AgrIA_server/assets/LLM_assets/`.

---

## 1. Current Architecture (as implemented)

### 1.1 Topology

```
START ──> deterministic_router (hybrid: fast-paths + LLM intent classifier)
              │
              ├─ basic_chat ──────────────────────> END
              ├─ app_usage ───────────────────────> END
              ├─ cap_query (RAG over regulatory KB) > END
              ├─ ecoschemes_rates (full rate table) > END
              ├─ fallback_rejection ──────────────> END
              ├─ report_generator ─> validate_report ─(loop back if invalid)─> END
              ├─ cap_document_inspector ─(inspector_edge)─> cap_application | cap_query
              ├─ cap_slot_guard ─(cap_guard_edge)─> cap_interruption | cap_application
              └─ cap_application ─────────────────> END
```

- Graph: `AgrIA_server/src/agent/graph.py` — `StateGraph(AgrIAState)`, compiled once at import with `MemorySaver` checkpointer (`AGRIA_GRAPH`).
- Entry: `POST /send-user-input` and `POST /load-parcel-data-to-chat` (`endpoints/chat.py`) → `generate_user_response` / `get_parcel_description` (`services/chat_service.py`) → `agent_graph.ainvoke(inputs, config={thread_id})`.
- State: `AgrIAState` (`models/state_models.py`) — `messages` (add_messages reducer), `lang`, `crop_metadata`, `cap_form_data`, `assessment_report`, `pending_action`, `cap_workflow`, `cap_alignment`, `cap_rates`, `visual_description`, `correction_feedback`.

### 1.2 The router (`agent/nodes/router_node.py::deterministic_router`)

Hybrid, in priority order:
1. **`pending_action` starts with `AWAITING_SLOT:`** → `cap_slot_guard` (zero LLM cost; the farmer is answering a form field).
2. **`pending_action == "AWAITING_CAP_DOC"`** → keyword sniff on last message ("pdf", "document", "formulario", "solicitud", …) → `cap_document_inspector`; otherwise `cap_application`.
3. **Empty message** → `basic_chat`.
4. **`###DESCRIBE_SHORT_IMAGE###` in text** → `report_generator` (system tag injected by the UI/chat service).
5. **LLM intent classifier** — one extra LLM call with `prompts/INTENT.md` (9 categories, JSON `{intent, confidence}`), last 4 turns of history, 25k token budget. Any parse/transport failure silently degrades to `basic_chat`.

### 1.3 The nodes

| Node | File | What it does | LLM calls |
|---|---|---|---|
| `basic_chat` | `nodes/basic_chat_node.py` | `execute_scoped_chat` with `ROLE.md` | 1 |
| `app_usage` | `nodes/app_usage_node.py` | `execute_scoped_chat` with `APP_USAGE.md` | 1 |
| `fallback_rejection` | `nodes/fallback_node.py` | `execute_scoped_chat` with `FALLBACK.md` | 1 |
| `cap_query` | `nodes/cap_query_node.py` | RAG: ChromaDB KB (`utils/rag_utils.py`, built from `assets/LLM_assets/context/files/*.md`) top-20 chunks → `CAP_QUERY.md` (es/en) | 1 |
| `ecoschemes_rates` | `nodes/ecoscheme_rates_node.py` | Injects the **entire** `prompts/classification.json` (EN+ES rate tables) → `RATES.md` | 1 |
| `report_generator` | `nodes/report_node.py` | `REPORT.md` (es/en) + `visual_description` + `crop_metadata` JSON | 1 (+retries) |
| `validate_report` | `nodes/validation_node.py` | **No LLM**: checks markdown table presence and that `Total_Parcel_Area_ha` appears in the report; loops back with `correction_feedback` otherwise | 0 |
| `cap_document_inspector` | `nodes/cap_document_inspector_node.py` | PDF text extraction (`pdfplumber` via `scripts/schema_extraction`) → LLM extraction constrained to `CAP_SLOTS.json` fields, reusing `CAP_SLOT_GUARD.md` as system prompt | 1 |
| `cap_slot_guard` | `nodes/cap_slot_guard_node.py` | One LLM call (`CAP_SLOT_GUARD.md`) returning `{classification, confidence, slots, reason}`; 2 attempts; deterministic fallback `_fallback_alignment` (schema-gated) when JSON is unusable | 1–2 |
| `cap_application` | `nodes/cap_application_node.py` | **Deterministic core**: merges guard slots into `cap_form_data`, runs `validate_application` (`utils/cap_form_utils.py`), asks exactly one next question (sets `AWAITING_SLOT:<name>`), or — once valid — builds `build_form_mapping` + `estimated_amounts` from `CAP_RATES.json` and lets the LLM only *narrate* the precomputed figures (`CAP_APPLICATION.md` + full `classification.json` + example form `context/forms/cap_form_redacted_JM_completed.md`) | 1 (only when valid) |
| `cap_interruption` | `nodes/cap_interruption_node.py` | Handles `pause` / `cancel` / `resume` / `topic_change` from the guard verdict; topic_change delegates to `basic_chat_node` while preserving form state | 0–1 |
| `clear_cap_workflow` | `nodes/router_node.py` | Node that resets `pending_action`/`cap_workflow`/`cap_alignment` | 0 |

### 1.4 Assets (`assets/LLM_assets/`)

- `prompts/` — the prompts-as-code folder (`BASE_PROMPTS_PATH`):
  - `INTENT.md` (router classifier, 9 intents, few-shot, JSON-only output)
  - `ROLE.md`, `APP_USAGE.md`, `FALLBACK.md`, `SUGGESTION.md` (stateless chat nodes)
  - `es/`+`en/`: `CAP_QUERY.md`, `REPORT.md` (bilingual)
  - `RATES.md`, `CAP_APPLICATION.md` (single-language, `{lang}` placeholder)
  - `CAP_SLOT_GUARD.md` (guard/inspector shared system prompt)
  - `CAP_SLOTS.json` (schema v1.0.0: 10 slots, bilingual questions + aliases; the **deterministic source of truth** for what the LLM may propose)
  - `CAP_RATES.json` (explicit €/ha table; `null` rates are dropped so unpublished rates never inflate amounts)
  - `classification.json` (EN+ES eco-scheme rules + rates, used by `cap_query` RAG context, `ecoschemes_rates`, and `cap_application`)
  - `examples/`, `old-examples/`, `LLM-full_desc_*`, `LLM-tldr_desc_*`, `prompt_list.json` (legacy Gemini-era assets, mostly unused by the graph)
- `context/files/` — regulatory markdown/PDF sources for the ChromaDB knowledge base (+ `context_document_links.json`)
- `context/forms/` — redacted CAP application forms (JSON/MD/PDF) used as few-shot examples and by the schema/anonymization scripts
- `skills/satellite-image-analysis/` — Hermes skill (image metrics) used by the VLM path, not by the graph

### 1.5 Supporting plumbing

- `LocalChat` (`models/chat_models.py`): wraps the OpenAI-compatible client (config `llm_client.py`, temperature 0.6), token counting, history summarization when >25k tokens.
- `get_recent_history(messages, max_turns)` (`utils/chat_utils.py`): **last-N-message window** (default 6, router/guard use 4). No summarization at this layer.
- `utils/cap_form_utils.py`: all deterministic form logic (slot schema, `parse_number` handling ES/EN decimals, `normalise_slots`, `merge_slots`, `validate_application`, `build_form_mapping`, `estimated_amounts`). Explicitly designed to be unit-testable without an LLM.
- `utils/rag_utils.py`: ChromaDB KB built from `context/files` (800-char chunks, 150 overlap), top-k retrieval.
- VLM path (`chat_service.py`): satellite image → (Hermes `AIAgent` skill or Gemini) visual description → `###DESCRIBE_*_IMAGE###` trigger → `report_generator`. PDF uploads are extracted with `pdfplumber` and appended to the user message (this is how `cap_document_inspector` receives a path).
- `endpoints/hermes_agent.py`: separate standalone Hermes chat router (not part of the graph).
- Suggestion endpoint (`/get-input-suggestion`): separate LLM call with `SUGGESTION.md` + chat summarizer, outside the graph.

---

## 2. What the current design does well

1. **The CAP workflow is genuinely deterministic at the core.** Slot extraction is *proposed* by the LLM but every value passes `normalise_slots`/`validate_application` (`cap_form_utils.py`); amounts are precomputed from `CAP_RATES.json` and the LLM is explicitly forbidden from inventing or rounding figures. This is the right pattern and it is well-isolated (unit-testable, 36 tests in `test/agent/test_cap_nodes.py`).
2. **Zero-LLM-cost fast paths** for the two most frequent in-workflow cases (answering a pending slot, resuming a doc request) — latency and cost stay flat during form filling.
3. **Guarded degradation**: guard JSON parse failure → 1 retry → deterministic fallback that still schema-gates values; router failure → `basic_chat`; PDF unreadable → ask for text. The form is never polluted by garbage.
4. **Prompts-as-code** in `LLM_assets/` with bilingual assets and a versioned slot schema (`schema_version`), so regulatory changes are content edits, not code edits.
5. **Isolated context windows per node** (each node rebuilds `LocalChat` with its own system prompt + last-N history) — a 25k report generation cannot bleed into a slot guard call.
6. **The report validation loop** (`validate_report`) is cheap (no LLM) and catches the two most common structural failures.
7. **Interruption handling is explicit** (pause/cancel/resume/topic_change as first-class guard verdicts) instead of an ad-hoc "is this still about the form?" heuristic in the main prompt.

## 3. What breaks or is under-covered as usage grows

### 3.1 The intent classifier is the single point of failure for everything

- **One extra LLM call on every non-fast-path turn**, with its own failure mode: any exception/timeout/malformed JSON silently degrades to `basic_chat`. A farmer saying "quiero solicitar los ecorregímenes" during a misclassification gets a generic chat answer with no form progress and no signal that routing failed. There is no telemetry distinguishing "model said basic_chat" from "classifier crashed".
- **9 categories with hard mutual exclusivity** is the core fragility. Real farmer messages are routinely multi-intent ("¿cuánto me pagan por P6 y cómo relleno la solicitud?" = `ecoschemes_rates` + `cap_application`). The prompt forces one label; the disambiguation tree is a heuristic baked into a prompt, not testable logic.
- **`cap_slot_guard` as a router intent is nearly dead weight**: when `pending_action` is set, fast-path #1 already routes to the guard deterministically. The classifier only sees it when `pending_action` is unset, in which case "a bare value answering the last question" has no question to answer — the category is self-contradictory in that state.
- **`confidence` is parsed but never used.** No threshold, no low-confidence escalation, no logging of near-misses. The classifier is all-or-nothing.
- **The classifier sees only the last 4 turns** (`get_recent_history(messages[:-1], max_turns=4)`), so intent that depends on earlier context ("sigue con lo del formulario") is out of reach.
- **Category drift is a prompt-only problem**: adding a use case = editing `INTENT.md` + a node + graph wiring + tests, with no shared registry — the valid-intent set is duplicated in three places (`VALID_INTENTS` Literal, `valid_intents` set in the same file, and the prompt's JSON schema line).

### 3.2 Workflow state is encoded as string markers, not a state machine

- `pending_action` is a free string ("AWAITING_SLOT:beneficiary.iban", "AWAITING_CAP_DOC") parsed with `split(":", 1)` and prefix checks in three files. `cap_workflow` ("collect"/"assess"/"ready"/"paused"/"cancelled"/"unrelated") is written by nodes but **read by nobody** — the router ignores it, so "paused" is only honored through the guard's `resume` classification, which requires the guard to have been routed first (i.e. `pending_action` still set).
- **`AWAITING_CAP_DOC` is dead state**: nothing in `src/` ever sets it (only the router consumes it and tests construct it). The document path is actually reached via the classifier or via PDF-appended text.
- **`clear_cap_workflow` is registered as a node but unreachable**: it is not in the router's edge map and no edge points to it. The only real clear paths are `cancel` (interruption node) and the implicit resets in `cap_query`/`cap_application`.
- **No explicit "abandon the form and ask something" path**: if the farmer changes topic mid-form, the guard says `topic_change` → `basic_chat` answers, but the form stays pending forever (by design, per the comments) — there is no timeout, no "are you still working on this?" nudge, and no way for the user to see the form's current state (no "show me what you have so far" intent exists).
- **No multi-parcel / multi-aid-line reality**: `CAP_SLOTS.json` models exactly one parcel (`parcels[].*` keys are flattened single values) and one eco-scheme practice, while `requested_aid_lines` is an array. A farmer with 3 parcels gets a form schema that cannot represent them; `build_form_mapping` hardcodes a single-element list.
- **`cap_query` clears `pending_action`** (comment: "farmer is back in advisory mode") — so asking a rule question mid-form *silently abandons* the form, contradicting the `topic_change` behavior which preserves it. The two "I asked something else" paths have opposite effects on workflow state.

### 3.3 Context management is a fixed window, not a policy

- Every node passes `get_recent_history(messages[:-1], 4..6)` — the last 4–6 raw messages. Consequences:
  - A farmer who gave their NIF 8 turns ago and returns to the form has it only in `cap_form_data` (good), but conversational commitments ("we agreed to apply for P6 and P7") are lost.
  - The router's 4-turn window means the classifier cannot see the assistant's last question in long exchanges, exactly when disambiguation is hardest.
  - `LocalChat` has a summarization fallback above 25k tokens, but the graph nodes rarely trigger it because the window is so small — the two mechanisms (window + summarizer) are redundant and neither is the primary policy.
- **`crop_metadata` is consumed once and nulled** by `validate_report` on PASSED. The parcel context is therefore single-use: a second report request in the same thread regenerates from whatever the UI re-sends, and `cap_application` after a report sees `crop_metadata=None` unless the UI re-injects it. The UI contract (which endpoint re-sends what) is implicit and fragile.
- **`assessment_report` is never cleared** — it persists across the whole thread and is injected into every `cap_application` final answer, even for a different parcel loaded later.

### 3.4 RAG and rate data are duplicated and partially stale

- Eco-scheme rules + rates live in **two places**: `prompts/classification.json` (injected verbatim into `ecoschemes_rates` and `cap_application`, and also the `OG_CLASSIFICATION_FILEPATH` constant) and the ChromaDB KB built from `context/files/*.md` (used by `cap_query`). They can disagree; there is no single source or version check. `RATES.md` even contains its own decision logic (thresholds, tiers) that duplicates what `classification.json` encodes.
- `ecoschemes_rates` injects the **entire** EN+ES classification JSON on every call (~4–5k tokens) regardless of the question; fine today, but it grows linearly with the number of schemes and languages.
- `cap_query` retrieves top-20 chunks (default `n_results=3` overridden) — no reranking, no citation of which document a rule came from, no freshness signal. Regulatory notes in `context/files` are dated (22/09/30, 23/03/06, 26/05/19) with no mechanism to invalidate superseded chunks.

### 3.5 Persistence and concurrency

- `MemorySaver` checkpointer: **all threads (including the CAP form state) vanish on process restart**. A farmer mid-application loses everything on a deploy. `thread_id` defaults to `"default_session"` in `chat_service.generate_user_response` and the `/send-user-input` endpoint does not accept one — so all users of that endpoint share one thread unless the UI uses `/load-parcel-data-to-chat` with a thread id. This is a correctness landmine for multi-user use.
- `chat_service._generate_user_response_sync` calls `asyncio.run(...)` inside `asyncio.to_thread` — works, but it means the graph is invoked from a worker thread with a fresh event loop per request; any shared async state (ChromaDB client, clients) must be thread-safe by luck of implementation.

### 3.6 Report path specifics

- `validate_report`'s Rule 2 (total area string must appear) is brittle: it string-matches the float in both `.` and `,` formats; a report that writes the area in words or with different precision fails and burns a retry loop with no max-retry cap (the loop is unbounded in the graph — `evaluation_router_edge` always returns `report_generator` on failure).
- The "no metadata" branch injects an instruction to insert `_Using last user message as land use metadata..._` into the report — a prompt-injection-style workaround for missing data that pollutes the report contract.
- The fast-path trigger `###DESCRIBE_SHORT_IMAGE###` is checked by substring in the router, but `###DESCRIBE_LONG_IMAGE###` (the detailed variant) is **not** — a detailed description request falls through to the LLM classifier, which is told the trigger means `report_generator`, so it works only if the model generalizes.

### 3.7 Coverage gaps (use cases with no home)

- **No "show my current application" / form status query** (the user cannot ask "¿qué llevo rellenado?").
- **No correction of the report** ("the area is wrong, it's 12 ha") — corrections only work inside the slot workflow; a report correction re-runs the whole generation with no targeted feedback channel (the `correction_feedback` state exists but is only written by `validate_report`).
- **No multi-turn task chaining**: every node is terminal (`→ END`), so "generate the report, then help me apply" requires the user to re-state intent and the router to re-classify; there is no plan/queue.
- **No escalation to a human / no confidence-based handoff** anywhere.
- **Language is a per-request form field**, not detected: a farmer who switches language mid-thread gets the `lang` of the latest request applied to *all* prompts, and the slot guard's bilingual schema is selected by that same field.
- **`app_usage` knowledge is frozen in `APP_USAGE.md`**: any UI change requires a prompt edit; the UI source of truth (Angular app) and the prompt can drift.

### 3.8 Asset hygiene (lower priority, but it muddies the decision layer)

- `prompt_list.json`, `LLM-full_desc_*`, `LLM-tldr_desc_*`, `LLM-role_prompt.txt`, `old-examples/` are legacy from the pre-LangGraph Gemini setup; `prompt_list.json` references files that are no longer the active prompts. `ROLE.md` (active) and `LLM-role_prompt.txt` (legacy) are near-duplicates.
- `context/forms/` contains both `.md` and `.json` and `.pdf` versions of the same redacted forms; only the `*_completed.md` is used at runtime.
- `skills/satellite-image-analysis/__pycache__` is committed.

---

## 4. Decision-level refactor options (no commitment)

The decision layer today = **router (intent) + string-marker workflow state + per-node prompts**. The options below are orthogonal axes; a final architecture picks one point per axis.

### Axis A — How intent is decided

| Option | Description | Pros | Cons / risks |
|---|---|---|---|
| **A1. Keep single-label classifier, harden it** | Use `confidence` (threshold + fallback policy), log all verdicts, dedupe the intent registry, expand context window, add a small eval set of real farmer messages run in CI | Minimal change; keeps the graph | Does not fix multi-intent; classifier remains a per-turn cost and failure point; category growth still requires prompt+node+edge changes |
| **A2. Multi-label / structured decision** | One LLM call returns `{intents: [...], workflow_action: enum, slots: {...}, confidence}` — i.e. merge the router and the slot guard into a single structured decision, with deterministic post-processing (schema gate, priority rules) | Eliminates the router/guard duplication; multi-intent is representable; one call instead of two on in-workflow turns | Bigger prompt to keep reliable; the deterministic post-processor becomes the real "decision layer" and needs its own tests; harder to debug which sub-decision failed |
| **A3. Agentic (tools) instead of pre-routed nodes** | One main agent with tools: `answer_cap_query`, `get_rates`, `generate_report`, `update_application`, `inspect_document`, `clarify_slot`…; the LLM decides which tool to call; guardrails become tool-level invariants (schema gate, rate table) | Natural multi-intent and chaining; adding a capability = adding a tool, not a node+edge+intent; the "guardrails don't cover all cases" problem shrinks because the agent can compose | Loses the deterministic fast paths (latency/cost per turn); harder to guarantee the CAP workflow invariants (needs tool-level enforcement + possibly a sub-graph); eval becomes harder; model capability matters more |
| **A4. Hybrid: deterministic workflow + agentic advisory** | Keep the CAP application as a deterministic sub-graph (it is the highest-stakes, most-validated part) but replace the 9-way intent router with an agent that can (a) enter/exit the CAP sub-graph, (b) call advisory tools, (c) answer directly | Keeps the strongest asset (deterministic form core) while removing the fragile 9-way classifier; multi-intent handled by the agent | Two decision paradigms to maintain; the enter/exit protocol between agent and sub-graph is a new design surface; needs careful state bridging |

**Key tradeoff**: A1/A2 buy reliability at the price of a closed category set (every new use case is a router change); A3/A4 buy openness at the price of per-turn LLM cost and weaker invariants. The current pain points (unreliable detector, guardrails that don't cover all cases) are *category-set* problems, which argues against A1 and for A2–A4. The highest-stakes flow (CAP form) is already deterministic and well-tested, which argues for **keeping it deterministic** (favoring A4 over A3).

### Axis B — How workflow state is represented

| Option | Description | Pros | Cons |
|---|---|---|---|
| **B1. Keep string markers, fix the bugs** | Make `cap_workflow` actually read by the router; remove dead `AWAITING_CAP_DOC`/`clear_cap_workflow` or wire them; unify the `cap_query` vs `topic_change` pending-action semantics | Minimal | String parsing stays; new workflow states keep accreting markers |
| **B2. Explicit state machine in state** | `cap_workflow` becomes a typed enum + a `form_progress` object (collected fields, last question, paused flag); the router becomes a pure function of `(workflow_state, message_features)` — no LLM needed while a workflow is active | Deterministic, testable, resumable; "show my form" becomes trivial; pause/resume/abandon become first-class transitions | Requires migrating existing threads (MemorySaver makes this cheap today — nothing to migrate); the LLM still decides *when* the user is talking about the form vs. not (that is Axis A's job) |
| **B3. Durable checkpointing** | Replace `MemorySaver` with a persistent checkpointer (SQLite/Postgres) and make `thread_id` mandatory per user/session | Form state survives deploys; multi-user correctness | Operational dependency; does not fix the state *model*, only its lifetime |

B2 and B3 are complementary (B2 is the model, B3 is the storage). B2 is the precondition for any of A2–A4 to be safe, because all of them rely on "is a workflow active?" being a cheap, reliable query.

### Axis C — Context policy

| Option | Description | Pros | Cons |
|---|---|---|---|
| **C1. Keep last-N window** | Status quo (4–6 messages) | Simple, cheap | Loses commitments; router blind in long threads |
| **C2. Role-based context assembly** | Each node declares which state slices it needs (form data, last report, parcel metadata, last K turns) and the assembly is explicit per node — i.e. make the implicit `get_recent_history` calls into a documented context contract | Predictable token budgets; fixes the `crop_metadata` single-use and `assessment_report` persistence problems by making them explicit decisions | More plumbing; needs a convention for what is "current parcel" vs "previous parcel" |
| **C3. Summarized long-term memory** | Periodic (or on-demand) summarization of the thread into a compact `conversation_summary` state field, plus the last-N window | Keeps long conversations coherent without huge windows | Summaries lose exact values (dangerous for a form assistant — exact values must live in structured state, not summaries, which B2 already guarantees) |

C2 is the decision-relevant one; C3 is optional sugar on top.

### Axis D — Knowledge source unification

| Option | Description | Pros | Cons |
|---|---|---|---|
| **D1. Single source of truth for rules+rates** | One versioned asset (e.g. the `classification.json` structure, or a superset) feeds: the RAG KB (chunked), the `ecoschemes_rates` injection (filtered by query), and `cap_application`. `CAP_RATES.json` becomes a projection of it. Dated documents get a `superseded_by` field. | Ends the two-copies drift; rate changes are one edit; enables "which document says this" citations | Requires a migration pass over `context/files` and `classification.json`; needs an owner/process for regulatory updates |
| **D2. Query-filtered injection** | Instead of injecting the whole EN+ES table, select the relevant scheme entries (by land use / practice mentioned) before the LLM call | Cuts tokens, scales with scheme count | Selection logic is another decision surface (can be deterministic from `crop_metadata`/land uses, which is cheap) |

### Axis E — Failure & evaluation policy (cross-cutting)

- **Telemetry**: log every routing verdict (intent, confidence, fast-path vs LLM, guard classification) with the thread id — today a misroute is invisible. This is prerequisite for *any* of the above and cheap to add.
- **Eval set**: a labeled set of real/representative farmer messages (multi-intent, mid-form, topic switches, ES/EN) run against the decision layer in CI. Without it, every change to the decision layer is unfalsifiable. The `old-examples/` folder is a seed.
- **Bounded retries**: cap the `validate_report` loop (max 2) and the guard retry (already 2) with a graceful degradation message.
- **Confidence policy**: define what happens at low confidence (ask a clarifying question vs. default to chat) — currently undefined.

### Indicative combinations (not a recommendation)

- **Conservative**: A1 + B1-fix + C2 + D1 + E — smallest diff, fixes the worst correctness bugs (thread sharing, dead state, unbounded loop, duplicated rates), still classifier-based.
- **Middle**: A2 + B2 + C2 + D1 + E — one structured decision call, explicit state machine, unified knowledge. The decision layer becomes: *deterministic state machine + one structured LLM decision + deterministic post-processing*.
- **Aggressive**: A4 + B2 + B3 + C2 + D1/D2 + E — deterministic CAP sub-graph + agentic advisory layer + durable state. Most future-proof for "guardrails that don't cover all cases", highest change surface.

## 5. Files (reference map for whichever option is chosen)

- `AgrIA_server/src/agent/graph.py` — topology; any Axis-A choice changes edges/nodes here.
- `AgrIA_server/src/agent/nodes/router_node.py` — `deterministic_router`, `cap_guard_edge`, `clear_cap_workflow`; the intent registry duplication lives here.
- `AgrIA_server/src/models/state_models.py` — `AgrIAState` + `CapSlotGuardOutput`; Axis B changes the state shape here.
- `AgrIA_server/src/agent/nodes/cap_slot_guard_node.py`, `cap_application_node.py`, `cap_document_inspector_node.py`, `cap_interruption_node.py` — CAP workflow; Axis A2/A4 changes how they are entered.
- `AgrIA_server/src/agent/nodes/{basic_chat,app_usage,fallback,cap_query,ecoscheme_rates,report,validation}_node.py` — advisory nodes; Axis A3/A4 turns these into tools.
- `AgrIA_server/src/utils/cap_form_utils.py` — deterministic core; **unchanged by any option** (it is the invariant layer).
- `AgrIA_server/src/utils/rag_utils.py`, `src/utils/chat_utils.py` (`get_recent_history`), `src/models/chat_models.py` (`LocalChat`) — Axis C/D touch these.
- `AgrIA_server/src/services/chat_service.py`, `src/endpoints/chat.py` — thread_id handling, PDF/image ingestion, triggers; Axis B3 and the `###DESCRIBE_LONG_IMAGE###` gap live here.
- `AgrIA_server/assets/LLM_assets/prompts/` — `INTENT.md` (Axis A), `CAP_SLOT_GUARD.md`, `CAP_SLOTS.json`, `CAP_RATES.json`, `classification.json` (Axis D), `RATES.md`, `CAP_QUERY.md` (es/en), `REPORT.md` (es/en), `ROLE.md`, `APP_USAGE.md`, `FALLBACK.md`, `SUGGESTION.md`; legacy: `prompt_list.json`, `LLM-*_prompt.txt`, `old-examples/`.
- `AgrIA_server/assets/LLM_assets/context/` — RAG sources + form examples (Axis D).
- `AgrIA_server/test/agent/` — `test_cap_graph.py` (10), `test_cap_nodes.py` (36), `test_graph_interaction.py` (5): the existing safety net for the CAP workflow; any Axis-A change must keep these green.

## 6. Testing (strategy, per option)

- **Keep green at all times**: `test/agent/test_cap_nodes.py`, `test_cap_graph.py`, `test_cap_form_utils.py` (deterministic core is the regression anchor).
- **New, regardless of option**: (a) router/decision-layer eval harness over a labeled message set (seed from `old-examples/` + new multi-intent/mid-form cases, ES+EN); (b) state-machine transition tests for Axis B (pause/resume/cancel/abandon/show-form, including the `cap_query`-vs-`topic_change` contradiction); (c) thread-isolation test proving two `thread_id`s cannot share form state; (d) unbounded-loop test proving the report retry is capped.
- **Per option**: A2/A4 need tool/decision contract tests (structured output schema + post-processor invariants); B3 needs a persistence round-trip test; D1 needs a consistency test asserting `CAP_RATES.json` and the KB derive from one source.

## 7. Implementation Order (template — instantiate after choosing the axes)

1. **Telemetry + eval harness (Axis E)** — prerequisite, no behavior change; makes every later step measurable.
2. **Correctness fixes independent of architecture**: mandatory `thread_id` per session; `###DESCRIBE_LONG_IMAGE###` fast path; bounded report-retry loop; remove or wire `clear_cap_workflow`; fix `cap_query` pending-action semantics; stop `validate_report` from nulling `crop_metadata` (or make re-injection explicit).
3. **Axis B (state model)** — typed workflow state + make the router a pure function of it; migrate `pending_action` consumers.
4. **Axis D (knowledge unification)** — single source for rules/rates; projection to `CAP_RATES.json`; supersession metadata.
5. **Axis A (decision layer)** — the chosen router replacement; keep the CAP sub-graph deterministic; update `INTENT.md` or replace it; update graph wiring.
6. **Axis C (context policy)** — per-node context contract; fix `assessment_report`/`crop_metadata` lifecycle.
7. **Axis B3 (durable checkpointing)** — last, once the state model is stable (migrating a moving state model is wasteful).
8. **Asset cleanup** — retire legacy prompts (`prompt_list.json`, `LLM-*_prompt.txt`, `old-examples/` → moved to an eval corpus), de-duplicate form assets, remove committed `__pycache__`.

---

*This plan deliberately stops at the decision level. The next step is choosing one point per axis (A–E) — the indicative combinations in §4 are the three realistic candidates — and then expanding the chosen combination into a concrete implementation plan with exact signatures and diffs.*
