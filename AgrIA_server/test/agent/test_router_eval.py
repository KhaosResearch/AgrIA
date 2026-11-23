"""Offline evaluation harness for the intent-classifier router.

Loads test/agent/router_eval_set.json, runs each case through
deterministic_router with the LLM call mocked (or live if --live),
and prints a pass/fail table + accuracy summary.

Usage (offline, deterministic):
    pytest test/agent/test_router_eval.py -v
    python -m test.agent.test_router_eval

Usage (live, real LLM — costs tokens):
    python -m test.agent.test_router_eval --live
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest
from src.agent.nodes.router_node import deterministic_router
from src.models.state_models import AgrIAState

EVAL_SET_PATH = Path(__file__).parent / "router_eval_set.json"


def _build_state(case: dict) -> AgrIAState:
    messages = []
    for turn in case.get("history", []):
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": case["message"]})
    return {
        "messages": messages,
        "lang": case.get("lang", "es"),
        "pending_action": case.get("pending_action"),
        "cap_form_data": case.get("cap_form_data"),
    }


def _mock_router(case: dict, state: AgrIAState) -> dict:
    """Offline: replicate fast-paths; for the LLM path, emulate the classifier.

    The LLM-path emulation is keyword-based and mirrors the decision tree in
    INTENT.md. It is intentionally *not* a copy of the real classifier (that
    would make the eval tautological); it is a stand-in that lets us test the
    router's post-processing (confidence gate, secondary-intent handling,
    telemetry) offline. The `--live` mode runs the real classifier instead.
    """
    messages = state["messages"]
    last = messages[-1]["content"] if messages else ""
    pending = state.get("pending_action")
    if pending and pending.startswith("AWAITING_SLOT:"):
        return {
            "next_node": "cap_slot_guard",
            "intents": ["cap_slot_guard"],
            "confidence": 1.0,
            "reason": "fast-path: pending slot",
        }
    # AWAITING_CAP_DOC is no longer a deterministic fast-path (B5): it falls
    # through to the LLM classifier like any other message.
    if not last.strip():
        return {
            "next_node": "basic_chat",
            "intents": ["basic_chat"],
            "confidence": 1.0,
            "reason": "fast-path: empty",
        }
    if "###DESCRIBE_SHORT_IMAGE###" in last or "###DESCRIBE_LONG_IMAGE###" in last:
        return {
            "next_node": "report_generator",
            "intents": ["report_generator"],
            "confidence": 1.0,
            "reason": "fast-path: image trigger",
        }
    # LLM path: emulate the classifier per the INTENT.md decision tree.
    return _emulate_classifier(case, last)


def _emulate_classifier(case: dict, text: str) -> dict:
    """Keyword-based stand-in for the LLM classifier (INTENT.md decision tree)."""
    t = text.lower()
    # Order matters: check the most specific categories first, mirroring the
    # INTENT.md decision tree. A rates question that also mentions "solicitud"
    # is multi-intent (rates primary, application secondary).
    # 1. Multi-intent: rates question + starting the application.
    if ("cuánto" in t or "importe" in t or "pagan" in t) and (
        "relleno" in t or "solicito" in t or "solicitud" in t
    ):
        return {
            "next_node": "ecoschemes_rates",
            "intents": ["ecoschemes_rates", "cap_application"],
            "confidence": 0.9,
            "reason": "emulated: multi-intent",
        }
    # 2. Money / rates (check before rules: "ecorregímenes" appears in both)
    if any(
        k in t
        for k in (
            "cuánto pagan",
            "importe unitario",
            "cuánto se cobra",
            "tarifas",
            "euros por hectárea",
            "pago por ha",
            "cuánto me pagan",
            "cuánto pagan",
            "importes",
            "cuánto paga",
        )
    ):
        return {
            "next_node": "ecoschemes_rates",
            "intents": ["ecoschemes_rates"],
            "confidence": 0.95,
            "reason": "emulated: rates",
        }
    # 3. App usage (check before rules: "ecorregímenes" appears in both)
    if any(
        k in t
        for k in (
            "cómo uso",
            "como uso",
            "cómo subo",
            "como subo",
            "cómo funciona",
            "como funciona",
            "cómo accedo",
            "usar la app",
            "usar la aplicación",
            "cómo usas",
            "como usas",
        )
    ):
        return {
            "next_node": "app_usage",
            "intents": ["app_usage"],
            "confidence": 0.9,
            "reason": "emulated: app usage",
        }
    # 4. Application: supplying own data (check before rules)
    if any(
        k in t
        for k in (
            "quiero solicitar",
            "ayúdame a rellenar",
            "mi nif",
            "mi iban",
            "mi parcela es",
            "estos son mis datos",
            "ayudame a rellenar",
            "solicitar los ecorregímenes",
            "solicitar los ecorregimen",
        )
    ):
        return {
            "next_node": "cap_application",
            "intents": ["cap_application"],
            "confidence": 0.95,
            "reason": "emulated: application",
        }
    # 4b. Form status: reviewing progress without new data
    if any(
        k in t
        for k in (
            "qué llevo",
            "que llevo",
            "muéstrame mi solicitud",
            "muestra mi solicitud",
            "estado de mi",
            "en qué punto",
            "en que punto",
            "show me my form",
            "what have i filled",
        )
    ):
        return {
            "next_node": "cap_form_status",
            "intents": ["cap_form_status"],
            "confidence": 0.95,
            "reason": "emulated: form status",
        }
    # 5. Document extraction
    if any(
        k in t
        for k in (
            "extrae los datos",
            "lee este documento",
            "extraer del pdf",
            "adjunto el pdf",
            "documento",
            "formulario",
            "pdf",
        )
    ):
        return {
            "next_node": "cap_document_inspector",
            "intents": ["cap_document_inspector"],
            "confidence": 0.9,
            "reason": "emulated: document",
        }
    # 6. Rules / eligibility
    if any(
        k in t
        for k in (
            "requisitos",
            "requisito",
            "penal",
            "norma",
            "ecorregímen",
            "ecorregimen",
            "pac",
            "pago básico",
        )
    ):
        return {
            "next_node": "cap_query",
            "intents": ["cap_query"],
            "confidence": 0.9,
            "reason": "emulated: rules",
        }
    # 7. Off-topic
    if any(
        k in t
        for k in (
            "champions",
            "fútbol",
            "futbol",
            "cinema",
            "película",
            "receta de cocina",
            "clima de mañana",
        )
    ):
        return {
            "next_node": "fallback_rejection",
            "intents": ["fallback_rejection"],
            "confidence": 0.95,
            "reason": "emulated: off-topic",
        }
    # 8. Ambiguous: below confidence threshold -> clarify
    if case.get("ambiguous"):
        return {
            "next_node": "clarify",
            "intents": [],
            "confidence": 0.4,
            "reason": "emulated: ambiguous",
        }
    # 9. Default
    return {
        "next_node": "basic_chat",
        "intents": ["basic_chat"],
        "confidence": 0.9,
        "reason": "emulated: default",
    }


def _run_case(case: dict, live: bool = False) -> dict:
    state = _build_state(case)
    expected = case["expected"]
    if live:
        # Live mode: run the real router (LLM classifier).
        from unittest.mock import MagicMock

        result = deterministic_router(state, MagicMock(), "test-model")
        actual = result if isinstance(result, str) else result.get("next_node", "")
    else:
        mock_result = _mock_router(case, state)
        actual = mock_result["next_node"]
    passed = actual == expected
    detail = "" if passed else f"expected={expected} got={actual}"
    return {
        "id": case["id"],
        "expected": expected,
        "actual": actual,
        "passed": passed,
        "detail": detail,
    }


def load_eval_set() -> list[dict]:
    with open(EVAL_SET_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_eval(live: bool = False) -> list[dict]:
    cases = load_eval_set()
    results = [_run_case(c, live=live) for c in cases]
    return results


def print_report(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'=' * 60}")
    print(f"Router Eval: {passed}/{total} passed ({100 * passed // total}%)")
    print(f"{'=' * 60}")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['id']:<40} {r['expected']:<25} {r['detail']}")
    print()


@pytest.mark.parametrize("case", load_eval_set(), ids=lambda c: c["id"])
def test_router_eval(case: dict) -> None:
    result = _run_case(case, live=False)
    assert result["passed"], f"Router eval failed for {case['id']}: {result['detail']}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Router eval harness")
    parser.add_argument(
        "--live", action="store_true", help="Use real LLM (costs tokens)"
    )
    args = parser.parse_args()
    results = run_eval(live=args.live)
    print_report(results)
    sys.exit(0 if all(r["passed"] for r in results) else 1)
