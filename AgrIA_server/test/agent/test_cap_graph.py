"""Graph-level tests for CAP routing, resumability and turn boundaries.

`inspector_edge` and the router's CAP branch are pure, so they are asserted
directly; the loop tests drive a freshly built graph with a stubbed chat model.
"""

from typing import cast
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.config import RunnableConfig

from src.agent.graph import inspector_edge
from src.agent.nodes.router_node import clear_cap_workflow, deterministic_router
from src.models.state_models import AgrIAState

# A complete application: `pending_action` still names a slot, so the next run
# must confirm readiness instead of asking another question.
READY_SLOTS = {
    "beneficiary.nif_cif": "12345678Z",
    "beneficiary.full_name": "Ana Ruiz",
    "beneficiary.iban": "ES91 2100 0418 4502 0005 1332",
    "parcels[].parcel_id": "26002A001000010000EQ",
    "parcels[].declared_crop": "Cebada",
    "parcels[].declared_surface_ha": 4.2,
    "parcels[].irrigation_type": "Regadio",
    "requested_aid_lines": ["AKR"],
}


# The slot guard and the application node share one chat model but want
# different shapes, so the stub keys off the payload it is given.
GUARD_VERDICT = (
    '{"classification": "answer", "confidence": 0.9, '
    '"slots": {"beneficiary.full_name": "Ana Ruiz"}, "reason": "states the name"}'
)


def _reply(text: str) -> MagicMock:
    """Stub a LocalChat reply carrying `text`."""
    response = MagicMock()
    response.text = text
    return response


def _stub_chat(monkeypatch, free_text: str) -> None:
    """Answer guard calls with a JSON verdict and summary calls with prose."""
    def _send(self, *args, **kwargs):
        payload = str(args[0]) if args else str(kwargs.get("message", ""))
        if "<allowed_fields>" in payload:
            return _reply(GUARD_VERDICT)
        return _reply(free_text)

    monkeypatch.setattr("src.models.chat_models.LocalChat.send_message", _send)


def _state(text: str = "hola", **overrides) -> AgrIAState:
    """Build a CAP-relevant state; the router and edges are pure over it."""
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


def _config(thread_id: str) -> RunnableConfig:
    return cast(RunnableConfig, {"configurable": {"thread_id": thread_id}, "recursion_limit": 12})


class TestInspectorEdge:
    def test_extracted_evidence_continues_to_application(self):
        alignment = {"classification": "answer", "slots": {"beneficiary.nif_cif": "1"}}
        assert inspector_edge(_state(cap_alignment=alignment)) == "cap_application"

    @pytest.mark.parametrize("alignment", [None, {}])
    def test_no_evidence_falls_back_to_advisory_query(self, alignment):
        assert inspector_edge(_state(cap_alignment=alignment)) == "cap_query"


class TestRouterDrivesCapChain:
    def test_pending_slot_goes_to_guard(self):
        state = _state("Ana Ruiz", pending_action="AWAITING_SLOT:beneficiary.full_name")
        assert deterministic_router(state, MagicMock(), "m") == "cap_slot_guard"

    def test_pending_slot_outranks_the_llm_router(self):
        """A pending question must never be re-classified by the LLM."""
        state = _state(
            "¿qué tiempo va a hacer?",
            pending_action="AWAITING_SLOT:beneficiary.full_name",
            cap_form_data={"beneficiary.nif_cif": "12345678Z"},
        )
        assert deterministic_router(state, MagicMock(), "m") == "cap_slot_guard"

    def test_pending_document_with_pdf_goes_to_inspector(self):
        state = _state("/tmp/solicitud.pdf", pending_action="AWAITING_CAP_DOC")
        assert deterministic_router(state, MagicMock(), "m") == "cap_document_inspector"

    def test_pending_document_without_pdf_goes_to_application(self):
        state = _state("no lo tengo", pending_action="AWAITING_CAP_DOC")
        assert deterministic_router(state, MagicMock(), "m") == "cap_application"

    def test_clear_cap_workflow_resets_every_cap_field(self):
        state = _state(pending_action="AWAITING_CAP_DOC", cap_workflow="collect")
        assert clear_cap_workflow(state) == {
            "pending_action": None,
            "cap_workflow": None,
            "cap_alignment": None,
        }


class TestCapTurnBoundaries:
    def test_clarification_question_ends_the_turn(self, monkeypatch):
        """One question per turn: no self-loop back into the application node."""
        from src.agent.graph import build_graph

        _stub_chat(monkeypatch, "Ana Ruiz")
        graph = build_graph().compile(checkpointer=MemorySaver())
        state = _state(
            "Ana Ruiz",
            cap_form_data={"beneficiary.nif_cif": "12345678Z"},
            pending_action="AWAITING_SLOT:beneficiary.full_name",
            cap_workflow="collect",
        )
        out = graph.invoke(state, _config("cap-collect"))

        replies = [m.content for m in out["messages"] if isinstance(m, AIMessage)]
        assert len(replies) == 1, "the node re-asked without a new farmer turn"
        assert out["cap_workflow"] == "collect"
        assert out["pending_action"].startswith("AWAITING_SLOT:")
        assert out["cap_form_data"]["beneficiary.full_name"] == "Ana Ruiz"

    def test_complete_application_reports_readiness_once(self, monkeypatch):
        from src.agent.graph import build_graph

        _stub_chat(monkeypatch, "Tu solicitud está lista.")
        graph = build_graph().compile(checkpointer=MemorySaver())
        state = _state(
            "listo",
            cap_form_data=READY_SLOTS,
            pending_action="AWAITING_SLOT:beneficiary.iban",
            cap_rates={"unit_rate_eur_ha": 120.5, "practice_rate_eur_ha": 80},
        )
        out = graph.invoke(state, _config("cap-ready"))

        replies = [m.content for m in out["messages"] if isinstance(m, AIMessage)]
        assert out["cap_workflow"] == "ready"
        assert out["pending_action"] is None
        assert replies == ["Tu solicitud está lista."]

    def test_pending_action_survives_the_turn_boundary(self, monkeypatch):
        """Resumability: the next invoke continues from the checkpointed question."""
        from src.agent.graph import build_graph

        _stub_chat(monkeypatch, "Ana Ruiz")
        graph = build_graph().compile(checkpointer=MemorySaver())
        config = _config("cap-resume")

        first = graph.invoke(
            _state(
                "Ana Ruiz",
                cap_form_data={"beneficiary.nif_cif": "12345678Z"},
                pending_action="AWAITING_SLOT:beneficiary.full_name",
                cap_workflow="collect",
            ),
            config,
        )
        assert first["cap_form_data"]["beneficiary.full_name"] == "Ana Ruiz"

        # The farmer answers the next question; the router must resume collection
        # from the checkpointed `pending_action` rather than start over.
        followup = cast(AgrIAState, {"messages": [HumanMessage(content="Ana Ruiz")]})
        second = graph.invoke(followup, config)
        assert second["cap_form_data"]["beneficiary.nif_cif"] == "12345678Z"
        assert second["cap_workflow"] == "collect"
        assert second["pending_action"].startswith("AWAITING_SLOT:")
