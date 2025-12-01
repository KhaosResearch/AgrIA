import pytest

from conftest import MOCK_CADASTRAL_REF, MOCK_GEOMETRY, MOCK_METADATA, MOCK_REG
from server.services.sigpac_tools_v2 import find as sigpac_find


@pytest.mark.parametrize(
    "test_name, cadastral_ref_input, read_reg_side_effect, search_return, expected_exception, expected_geometry, expected_metadata",
    [
        pytest.param(
            "Success_ValidRef",
            MOCK_CADASTRAL_REF,
            MOCK_REG,
            # MOCK_GEOMETRY and MOCK_METADATA from conftest
            (MOCK_GEOMETRY, MOCK_METADATA),
            None,
            MOCK_GEOMETRY,
            MOCK_METADATA,
            id="Success_Found"
        ),
        pytest.param(
            "Failure_NotFound",
            MOCK_CADASTRAL_REF,
            {"province": "99", "municipality": "999"},
            ([], []),  # Search returns empty data
            ValueError,
            None,
            None,
            id="Failure_NotFound"
        ),

        pytest.param(
            "Failure_UrbanCadastralRef",
            "999999999999999999ZQ",
            {"province": "99", "municipality": "999"},
            ([], []),  # Search returns empty data
            NotImplementedError,
            None,
            None,
            id="Failure_UrbanCadastralRef"
        ),
        pytest.param(
            "Failure_InvalidCadastralRef",
            "SHORT_REF",
            None,  # The mock function should be set to raise the ValueError directly
            (MOCK_GEOMETRY, MOCK_METADATA),
            ValueError,
            None,
            None,
            id="Failure_InvalidCadastralRef"
        ),
    ]
)
def test_find_from_cadastral_registry_scenarios(
    mock_sigpact_tools_v2_dependencies, monkeypatch,
    test_name, cadastral_ref_input, read_reg_side_effect, search_return,
    expected_exception, expected_geometry, expected_metadata
):
    # --- ARRANGE (Conditional Mocks) ---
    # Retrieve mocks
    mock_read = mock_sigpact_tools_v2_dependencies["mock_read_cadastral_registry"]
    mock_search = mock_sigpact_tools_v2_dependencies["mock_search"]

    # Reset mocks
    mock_read.reset_mock()
    mock_search.reset_mock()

    # --- ARRANGE (Conditional Mocks) ---

    # 1. Handle failure cases that raise inside read_cadastral_registry (Urban/Invalid Ref)
    if "UrbanCadastralRef" in test_name:
        # Simulate the NotImplementedError that happens inside validate_cadastral_registry
        mock_read.side_effect = NotImplementedError(
            "If the reference is urban"
        )

    elif "InvalidCadastralRef" in test_name:
        # Simulate the ValueError (e.g., length check) that happens inside read_cadastral_registry
        mock_read.side_effect = ValueError(
            "The cadastral reference must have a length of 20 characters"
        )

    # 2. Handle success and not-found cases (where read_cadastral_registry succeeds)
    else:
        # Set the return value for the mock
        mock_read.return_value = read_reg_side_effect
        mock_search.return_value = search_return

        # Ensure no lingering side effects from previous failure tests
        mock_read.side_effect = None
        mock_search.side_effect = None

    # --- ACT & ASSERT ---
    if expected_exception:
        # Expected Failure
        with pytest.raises(expected_exception):
            sigpac_find.find_from_cadastral_registry(cadastral_ref_input)

        # Assertion for failures
        if "UrbanCadastralRef" in test_name or "InvalidCadastralRef" in test_name:
            # If the exception is raised by the mock, it was called once
            mock_read.assert_called_once()
            # Search is not called because the function raises before that line
            mock_search.assert_not_called()
        elif "NotFound" in test_name:
            # read_cadastral_registry is called, search is called, but search returns []/[]
            mock_read.assert_called_once()
            mock_search.assert_called_once()

    else:
        # Expected Success
        geometry, metadata = sigpac_find.find_from_cadastral_registry(
            cadastral_ref_input)

        # 1. Check return values
        assert geometry == expected_geometry

        # 2. Check the metadata was modified correctly to include the input reference
        assert metadata['parcelaInfo']['referencia_cat'] == cadastral_ref_input

        # 3. Verify mocks were called (Fix for previous assertion error)
        mock_read.assert_called_once_with(cadastral_ref_input)
        mock_search.assert_called_once()
