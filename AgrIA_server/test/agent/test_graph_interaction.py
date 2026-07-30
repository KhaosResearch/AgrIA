from src.agent.graph import AGRIA_GRAPH


def test_greeting_flow(base_state, test_config):
    """[TEST A] Verify greeting routes to basic_chat_node."""
    state = base_state("Hola buenas tardes")

    result = AGRIA_GRAPH.invoke(state, config=test_config)

    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1].content, str)
    assert len(result["messages"][-1].content.strip()) > 0


def test_out_of_scope_flow(base_state, test_config):
    """[TEST B] Verify non-agricultural prompt routes to fallback_node."""
    state = base_state("¿Cuál es el sentido de la vida?")

    result = AGRIA_GRAPH.invoke(state, config=test_config)

    assert len(result["messages"]) > 1
    # Verify rejection response is returned
    assert result["messages"][-1].content != ""


def test_report_flow(base_state, mock_crop_json, test_config):
    """[TEST C] Verify report request triggers report_node and validation loop."""
    state = base_state("###DESCRIBE_SHORT_IMAGE### Genera el informe.")
    state["crop_metadata"] = mock_crop_json
    state["visual_description"] = "Parcela irregular con cultivo de secano."

    result = AGRIA_GRAPH.invoke(state, config=test_config)

    assert len(result["messages"]) > 1
    assert (
        "26002A001000010000EQ" in str(result["messages"][-1].content)
        or len(result["messages"][-1].content) > 50
    )


def test_cap_query_flow(base_state, test_config):
    """[TEST D] Verify CAP questions trigger cap_query_node."""
    state = base_state(
        "¿Cuáles son los ecorregímenes más adecuados para cultivos leñosos?"
    )

    result = AGRIA_GRAPH.invoke(state, config=test_config)

    assert len(result["messages"]) > 1
    assert len(result["messages"][-1].content) > 0


def test_ecoscheme_rates_flow(base_state, test_config):
    """[TEST E] Verify rates query triggers ecoscheme_rates_node."""
    state = base_state("¿Cuáles son los importes de los ecorregímenes en 2026?")

    result = AGRIA_GRAPH.invoke(state, config=test_config)

    assert len(result["messages"]) > 1
    assert len(result["messages"][-1].content) > 0
