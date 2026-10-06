"""Unit tests for the CAP clarification nodes: inspector, guard and application.

All LLM output is stubbed, so these tests assert deterministic behaviour only:
schema gating, evidence handling, resumability and the pending-action contract.
"""

from typing import cast
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.nodes.cap_application_node import cap_application_node
from src.agent.nodes.cap_document_inspector_node import (
    _pdf_path_from,
    _parse_slots,
    cap_document_inspector_node,
)
from src.agent.nodes.cap_slot_guard_node import (
    cap_slot_guard_node,
    guard_ack,
    next_slot_prompt,
    pending_slot_name,
    topic_change_message,
)
from src.agent.nodes.router_node import clear_cap_workflow, deterministic_router
from src.models.state_models import AgrIAState

RATES = {"unit_rate_eur_ha": "120,50", "practice_rate_eur_ha": 80}

# One farmer reply supplying everything except the IBAN.
COMPLETE_EXCEPT_IBAN = {
    "beneficiary.nif_cif": "12345678Z",
    "beneficiary.full_name": "Ana Ruiz",
    "parcels[].parcel_id": "26002A001000010000EQ",
    "parcels[].declared_crop": "Cebada",
    "parcels[].declared_surface_ha": 4.2,  # stored normalised, as merge_slots leaves it
    "parcels[].irrigation_type": "Regadio",
    "requested_aid_lines": ["AKR"],
}


def _reply(text: str) -> MagicMock:
    """Stub a LocalChat reply carrying `text`."""
    response = MagicMock()
    response.text = text
    return response


def _state(text: str = "hola", **overrides) -> AgrIAState:
    state = {
        "messages": [HumanMessage(content=text)],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
        "correction_feedback": None,
        "cap_form_data": None,
        "pending_action": None,
        "cap_alignment": None,
        "cap_workflow": None,
        "cap_rates": None,
    }
    state.update(overrides)
    return cast(AgrIAState, state)


class TestPdfPathDiscovery:
    @pytest.mark.parametrize(
        "content, expected",
        [
            ("/tmp/solicitud.pdf", "/tmp/solicitud.pdf"),
            ([{"file_path": "/tmp/doc.PDF"}], "/tmp/doc.PDF"),
            ({"document": "/tmp/x.pdf"}, "/tmp/x.pdf"),
            ([{"type": "text", "text": "hola"}, {"url": "/tmp/y.pdf"}], "/tmp/y.pdf"),
        ],
    )
    def test_extracts_pdf_path(self, content, expected):
        assert _pdf_path_from(content) == expected

    @pytest.mark.parametrize("content", ["", "/tmp/formulario.docx", [{"text": "hola"}], None])
    def test_returns_none_without_pdf(self, content):
        assert _pdf_path_from(content) is None


class TestSlotParsing:
    def test_parses_bare_json(self):
        assert _parse_slots('{"a": 1}') == {"a": 1}

    def test_parses_fenced_json_with_prose(self):
        reply = '```json\n{"a": 2}\n```\nHope that helps.'
        assert _parse_slots(reply) == {"a": 2}

    @pytest.mark.parametrize("reply", ["", "no json here", "{broken", "[1, 2]", "{'a': 1}"])
    def test_tolerates_unparseable_replies(self, reply):
        assert _parse_slots(reply) == {}


class TestDocumentInspector:
    def test_ignores_non_human_message(self):
        state = _state()
        state["messages"] = [AIMessage(content="¿NIF?")]
        assert cap_document_inspector_node(state, MagicMock(), "m") == {"cap_alignment": None}

    def test_ignores_message_without_pdf(self):
        result = cap_document_inspector_node(_state("hola"), MagicMock(), "m")
        assert result == {"cap_alignment": None}

    def test_extracts_only_supported_slots(self, monkeypatch):
        monkeypatch.setattr(
            "src.agent.nodes.cap_document_inspector_node._read_pdf_text",
            lambda path: "NIF 12345678Z. Parcel 26002A001000010000EQ de 4,2 ha de cebada en regadio.",
        )
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply(
                '{"classification": "answer", "confidence": 1.0, "slots": '
                '{"beneficiary.nif_cif": "12345678Z", "beneficiary.salary": "9999"}, "reason": "doc"}'
            ),
        )
        result = cap_document_inspector_node(_state("/tmp/a.pdf"), MagicMock(), "m")
        slots = result["cap_alignment"]["slots"]
        assert slots == {"beneficiary.nif_cif": "12345678Z"}
        assert result["cap_workflow"] == "collect"

    def test_unreadable_pdf_asks_for_text_without_inventing(self, monkeypatch):
        monkeypatch.setattr(
            "src.agent.nodes.cap_document_inspector_node._read_pdf_text",
            lambda path: "",
        )
        result = cap_document_inspector_node(_state("/tmp/a.pdf", lang="en"), MagicMock(), "m")
        assert "cap_form_data" not in result
        assert "PDF" in result["messages"][0].content

    def test_llm_failure_degrades_to_no_alignment(self, monkeypatch):
        monkeypatch.setattr(
            "src.agent.nodes.cap_document_inspector_node._read_pdf_text",
            lambda path: "NIF 12345678Z",
        )

        def _boom(self, *a, **k):
            raise RuntimeError("provider down")

        monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _boom)
        assert cap_document_inspector_node(_state("/tmp/a.pdf"), MagicMock(), "m") == {
            "cap_alignment": None
        }


class TestSlotGuard:
    def test_empty_message_is_missing_information(self):
        result = cap_slot_guard_node(_state("   "), MagicMock(), "m")
        assert result["cap_alignment"]["classification"] == "missing_information"

    def test_accepts_answer_with_supported_slots(self, monkeypatch):
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply(
                '{"classification": "correction", "confidence": 0.8, "slots": '
                '{"parcels[].declared_surface_ha": "3.000,25 ha", "nope": 1}, "reason": "corrige"}'
            ),
        )
        alignment = cap_slot_guard_node(_state("son 3.000,25 ha"), MagicMock(), "m")[
            "cap_alignment"
        ]
        assert alignment["classification"] == "correction"
        assert alignment["slots"] == {"parcels[].declared_surface_ha": 3000.25}

    def test_unknown_classification_becomes_topic_change(self, monkeypatch):
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply('{"classification": "banana", "confidence": 2, "slots": {}}'),
        )
        alignment = cap_slot_guard_node(_state("hola"), MagicMock(), "m")["cap_alignment"]
        assert alignment["classification"] == "topic_change"
        assert alignment["confidence"] == 1.0

    def test_unparseable_reply_retries_then_falls_back(self, monkeypatch):
        """A malformed classifier reply must not cost the farmer their answer."""
        replies = iter(["no json", "still no json"])
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply(next(replies)),
        )
        state = _state("Ana Ruiz")
        state["pending_action"] = "AWAITING_SLOT:beneficiary.full_name"
        state["cap_form_data"] = {"beneficiary.nif_cif": "12345678Z"}

        alignment = cap_slot_guard_node(state, MagicMock(), "m")["cap_alignment"]
        assert alignment["classification"] == "answer"
        assert alignment["slots"] == {"beneficiary.full_name": "Ana Ruiz"}

    def test_second_attempt_can_succeed(self, monkeypatch):
        replies = iter(["no json", '{"classification": "answer", "slots": {"beneficiary.iban": "ES91"}}'])
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply(next(replies)),
        )
        alignment = cap_slot_guard_node(_state("ES91"), MagicMock(), "m")["cap_alignment"]
        assert alignment["slots"] == {"beneficiary.iban": "ES91"}

    def test_fallback_rejects_text_that_fails_validation(self, monkeypatch):
        """The deterministic path still has to refuse an invalid value."""
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply("no json"),
        )
        state = _state("not a surface at all")
        state["pending_action"] = "AWAITING_SLOT:parcels[].declared_surface_ha"
        alignment = cap_slot_guard_node(state, MagicMock(), "m")["cap_alignment"]
        assert alignment["classification"] == "topic_change"
        assert alignment["slots"] == {}

    def test_fallback_without_pending_slot_is_a_topic_change(self, monkeypatch):
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply("no json"),
        )
        alignment = cap_slot_guard_node(_state("Ana Ruiz"), MagicMock(), "m")["cap_alignment"]
        assert alignment["classification"] == "topic_change"


class TestPendingActionHelpers:
    def test_pending_slot_name(self):
        assert pending_slot_name("AWAITING_SLOT:beneficiary.iban") == "beneficiary.iban"
        assert pending_slot_name("AWAITING_SLOT:") is None
        assert pending_slot_name(None) is None

    def test_next_slot_prompt_is_localised(self):
        assert "IBAN" in next_slot_prompt("AWAITING_SLOT:beneficiary.iban", "en")
        assert "IBAN" in next_slot_prompt("AWAITING_SLOT:beneficiary.iban", "es")

    def test_next_slot_prompt_ignores_other_actions(self):
        assert next_slot_prompt("AWAITING_CAP_DOC", "es") == ""

    def test_guard_ack_lists_written_fields(self):
        slots = {"beneficiary.nif_cif": "12345678Z", "requested_aid_lines": ["AKR"]}
        ack = guard_ack(slots, list(slots), "es")
        assert "12345678Z" in ack and "AKR" in ack

    def test_guard_ack_is_empty_without_changes(self):
        assert guard_ack({}, [], "en") == ""

    def test_topic_change_message_is_localised(self):
        assert "CAP" in topic_change_message("en")
        assert "CAP" in topic_change_message("es")


class TestRouterPrecedence:
    def test_pending_slot_outranks_llm_router(self):
        state = _state("12345678Z", pending_action="AWAITING_SLOT:beneficiary.nif_cif")
        assert deterministic_router(state, MagicMock(), "m") == "cap_slot_guard"

    def test_pending_cap_doc_pdf_goes_to_inspector(self):
        state = _state("aqui va mi documento pdf", pending_action="AWAITING_CAP_DOC")
        assert deterministic_router(state, MagicMock(), "m") == "cap_document_inspector"

    def test_pending_cap_doc_other_reply_goes_to_application(self):
        state = _state("no lo tengo", pending_action="AWAITING_CAP_DOC")
        assert deterministic_router(state, MagicMock(), "m") == "cap_application"

    def test_clear_cap_workflow_resets_state(self):
        state = _state(pending_action="AWAITING_SLOT:beneficiary.iban", cap_workflow="collect")
        assert clear_cap_workflow(state) == {
            "pending_action": None,
            "cap_workflow": None,
            "cap_alignment": None,
        }


class TestApplicationNode:
    def test_asks_for_next_required_field(self):
        result = cap_application_node(_state("12345678Z"), MagicMock(), "m")
        assert result["cap_workflow"] == "collect"
        assert result["pending_action"].startswith("AWAITING_SLOT:")
        assert "messages" in result

    def test_does_not_touch_slots_on_topic_change(self):
        slots = {"beneficiary.nif_cif": "12345678Z"}
        state = _state(
            "¿qué tiempo va a hacer?",
            cap_form_data=slots,
            pending_action="AWAITING_SLOT:beneficiary.full_name",
            cap_alignment={"classification": "topic_change", "slots": {}},
        )
        result = cap_application_node(state, MagicMock(), "m")
        assert "cap_form_data" not in result
        assert "pending_action" not in result
        assert result["messages"][0].content == topic_change_message("es")

    def test_missing_iban_asks_for_iban(self):
        alignment = {"classification": "answer", "slots": dict(COMPLETE_EXCEPT_IBAN)}
        state = _state("mis datos", cap_alignment=alignment, cap_rates=RATES)
        result = cap_application_node(state, MagicMock(), "m")
        assert result["pending_action"] == "AWAITING_SLOT:beneficiary.iban"

    def test_valid_application_reports_reproduced_amounts(self, monkeypatch):
        captured = {}

        def _capture(self, *a, **k):
            captured["payload"] = str(a[0]) if a else ""
            return _reply("Estimated 666.10 EUR in total.")

        monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _capture)
        slots = {**COMPLETE_EXCEPT_IBAN, "beneficiary.iban": "ES91 2100 0418 4502 0005 1332"}
        state = _state("todo listo", cap_form_data=slots, cap_rates=RATES)
        result = cap_application_node(state, MagicMock(), "m")

        assert result["cap_workflow"] == "ready"
        assert result["pending_action"] is None
        assert result["messages"][0].content == "Estimated 666.10 EUR in total."
        # Amounts handed to the LLM are the reproducible ones, computed in Python:
        # 4.2 ha x 120.50 = 506.10 base, 4.2 ha x 80.00 = 336.00 eco, 842.10 total.
        assert '"estimated_base_eur": 506.1' in captured["payload"]
        assert '"estimated_eco_scheme_eur": 336.0' in captured["payload"]
        assert '"estimated_total_eur": 842.1' in captured["payload"]

    def test_no_rates_means_no_amount(self, monkeypatch):
        captured = {}

        def _capture(self, *a, **k):
            captured["payload"] = str(a[0]) if a else ""
            return _reply("Your application is ready.")

        monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _capture)
        slots = {**COMPLETE_EXCEPT_IBAN, "beneficiary.iban": "ES91 2100 0418 4502 0005 1332"}
        result = cap_application_node(_state("todo listo", cap_form_data=slots), MagicMock(), "m")

        assert result["cap_workflow"] == "ready"
        # Without an explicit rate table the agent must not invent a figure.
        assert "estimated_base_eur" not in captured["payload"]

    def test_shipped_rate_asset_is_used_when_state_has_no_rates(self, monkeypatch):
        """No state rates -> fall back to the versioned asset, not to a guess."""
        captured: dict = {}

        def _capture(self, *a, **k):
            captured["payload"] = str(a[0]) if a else ""
            return _reply("Your application is ready.")

        monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _capture)
        slots = {**COMPLETE_EXCEPT_IBAN, "beneficiary.iban": "ES91 2100 0418 4502 0005 1332"}
        result = cap_application_node(_state("todo listo", cap_form_data=slots), MagicMock(), "m")

        assert result["cap_workflow"] == "ready"
        # The shipped asset publishes no base/practice rate, so still no figure.
        assert "estimated_base_eur" not in captured["payload"]

    def test_state_rates_take_precedence_over_the_asset(self, monkeypatch):
        captured: dict = {}

        def _capture(self, *a, **k):
            captured["payload"] = str(a[0]) if a else ""
            return _reply("Your application is ready.")

        monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _capture)
        slots = {**COMPLETE_EXCEPT_IBAN, "beneficiary.iban": "ES91 2100 0418 4502 0005 1332"}
        cap_application_node(_state("listo", cap_form_data=slots, cap_rates=RATES), MagicMock(), "m")

        assert '"estimated_base_eur": 506.1' in captured["payload"]

    def test_reply_does_not_leak_internal_field_names(self, monkeypatch):
        """Internal slot identifiers must never reach the farmer."""
        monkeypatch.setattr(
            "src.models.chat_models.LocalChat.send_message",
            lambda self, *a, **k: _reply("What is your full name?"),
        )
        result = cap_application_node(_state("12345678Z"), MagicMock(), "m")

        content = result["messages"][0].content
        assert "missing_required" not in content
        assert "beneficiary.full_name" not in content

    def test_alignment_is_consumed_after_merge(self):
        alignment = {"classification": "answer", "slots": {"beneficiary.nif_cif": "12345678Z"}}
        result = cap_application_node(_state("12345678Z", cap_alignment=alignment), MagicMock(), "m")
        assert result["cap_alignment"] is None
        assert result["cap_form_data"]["beneficiary.nif_cif"] == "12345678Z"
