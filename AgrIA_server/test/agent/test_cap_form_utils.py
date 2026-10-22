"""Unit tests for the deterministic CAP form helpers.

These cover parsing, schema gating, merging, completeness and amount
reproduction without any LLM involvement.
"""

import pytest

from src.utils.cap_form_utils import (
    build_form_mapping,
    coerce_value,
    estimated_amounts,
    first_missing_slot,
    is_valid_slot,
    load_cap_rates,
    load_cap_slots,
    merge_slots,
    missing_required_slots,
    normalise_slots,
    parse_number,
    slot_definition,
    validate_application,
)

# A complete, valid application used as the base for "should pass" assertions.
VALID_SLOTS = {
    "beneficiary.nif_cif": "12345678Z",
    "beneficiary.full_name": "Ana Ruiz",
    "beneficiary.iban": "ES91 2100 0418 4502 0005 1332",
    "parcels[].parcel_id": "26002A001000010000EQ",
    "parcels[].declared_crop": "trigo",
    "parcels[].declared_surface_ha": 4.2,
    "parcels[].irrigation_type": "Regadio",
    "eco_schemes[].practice_code": "AG-ECO-01",
    "eco_schemes[].applied_surface_ha": 2.0,
    "requested_aid_lines": ["base"],
}


# --------------------------------------------------------------------------- #
# Schema loading
# --------------------------------------------------------------------------- #
class TestSchemaLoading:
    def test_schema_is_versioned(self):
        _, version = load_cap_slots()
        assert version

    def test_required_slots_are_declared(self):
        schema = load_cap_slots()[0]
        required = [name for name, spec in schema.items() if spec["required"]]
        assert required, "the CAP schema must declare required fields"

    def test_bilingual_questions_present(self):
        for name, spec in load_cap_slots()[0].items():
            assert spec["question_es"], f"{name} missing Spanish question"
            assert spec["question_en"], f"{name} missing English question"

    def test_unknown_slot_is_not_valid(self):
        assert is_valid_slot("beneficiary.nif_cif") is True
        assert is_valid_slot("beneficiary.not_a_field") is False
        assert slot_definition("beneficiary.not_a_field") is None


# --------------------------------------------------------------------------- #
# Number parsing (ES/EN conventions)
# --------------------------------------------------------------------------- #
class TestParseNumber:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("4.2", 4.2),
            ("4,2", 4.2),
            ("1.234", 1234.0),
            ("1,500", 1500.0),
            ("12,345.67", 12345.67),
            ("12.345,67", 12345.67),
            ("3.000,25", 3000.25),
            ("1.234,5 ha", 1234.5),
            ("4.2 ha", 4.2),
            (7, 7.0),
            (7.5, 7.5),
        ],
    )
    def test_parses_both_locales(self, raw, expected):
        assert parse_number(raw) == pytest.approx(expected)

    def test_prefers_explicit_hectare_value_over_parcel_id(self):
        # A cadastral reference contains digits that must not be mistaken for a surface.
        assert parse_number("26002A001000010000EQ: 3,000,25 ha") == pytest.approx(
            3000.25
        )

    def test_percent_sign_ignored(self):
        assert parse_number("45%") == pytest.approx(45.0)

    @pytest.mark.parametrize("raw", ["", "sin datos", None, True, "N/A"])
    def test_unparseable_values_return_none(self, raw):
        assert parse_number(raw) is None


# --------------------------------------------------------------------------- #
# Coercion and schema gating
# --------------------------------------------------------------------------- #
class TestCoercion:
    def test_number_slot_accepts_locale_string(self):
        assert coerce_value(
            "parcels[].declared_surface_ha", "1.234,5"
        ) == pytest.approx(1234.5)

    def test_array_slot_splits_on_comma(self):
        assert coerce_value("requested_aid_lines", "base, eco") == ["base", "eco"]

    def test_array_slot_preserves_list(self):
        assert coerce_value("requested_aid_lines", ["base"]) == ["base"]

    def test_enum_accepts_loose_spelling(self):
        assert coerce_value("parcels[].irrigation_type", "de regadio") == "Regadio"

    def test_enum_rejects_unknown_value(self):
        assert coerce_value("parcels[].irrigation_type", "hidropónico") is None

    def test_unknown_slot_coerces_to_none(self):
        assert coerce_value("not.a.field", "x") is None


class TestNormaliseSlots:
    def test_drops_unknown_fields(self):
        result = normalise_slots(
            {"beneficiary.nif_cif": "12345678Z", "evil_field": "x"}
        )
        assert result == {"beneficiary.nif_cif": "12345678Z"}

    def test_drops_uncoercible_values(self):
        result = normalise_slots({"parcels[].irrigation_type": "hidropónico"})
        assert result == {}

    def test_coerces_numbers(self):
        result = normalise_slots({"parcels[].declared_surface_ha": "12,5"})
        assert result["parcels[].declared_surface_ha"] == pytest.approx(12.5)

    @pytest.mark.parametrize("payload", [None, "not a dict", 42, []])
    def test_non_dict_input_yields_empty(self, payload):
        assert normalise_slots(payload) == {}


# --------------------------------------------------------------------------- #
# Merging
# --------------------------------------------------------------------------- #
class TestMergeSlots:
    def test_incoming_overrides_existing(self):
        merged = merge_slots(
            {"beneficiary.full_name": "Ana"}, {"beneficiary.full_name": "Eva"}
        )
        assert merged["beneficiary.full_name"] == "Eva"

    def test_empty_values_do_not_clear_prior_value(self):
        merged = merge_slots(
            {"beneficiary.full_name": "Ana"},
            {"beneficiary.full_name": "", "requested_aid_lines": []},
        )
        assert merged["beneficiary.full_name"] == "Ana"
        assert "requested_aid_lines" not in merged

    def test_merge_of_nothing_is_empty(self):
        assert merge_slots(None, None) == {}


# --------------------------------------------------------------------------- #
# Completeness and validation
# --------------------------------------------------------------------------- #
class TestValidation:
    def test_complete_application_is_valid(self):
        report = validate_application(VALID_SLOTS)
        assert report["valid"] is True
        assert report["errors"] == []

    def test_missing_required_fields_are_reported(self):
        report = validate_application({})
        assert report["valid"] is False
        assert set(report["missing_required"]) == set(missing_required_slots({}))

    def test_first_missing_slot_follows_schema_order(self):
        first = first_missing_slot({}, "es")
        assert first is not None
        assert first["name"] == missing_required_slots({})[0]

    def test_first_missing_slot_is_localised(self):
        english, spanish = first_missing_slot({}, "en"), first_missing_slot({}, "es")
        assert english is not None and spanish is not None
        assert english["question"] != spanish["question"]

    def test_first_missing_slot_none_when_complete(self):
        assert first_missing_slot(VALID_SLOTS, "es") is None

    def test_invalid_enum_is_an_error(self):
        slots = {**VALID_SLOTS, "parcels[].irrigation_type": "Riego alternativo"}
        report = validate_application(slots)
        assert report["valid"] is False
        assert any(err.startswith("invalid_value:") for err in report["errors"])

    def test_eco_surface_cannot_exceed_parcel(self):
        slots = {**VALID_SLOTS, "eco_schemes[].applied_surface_ha": 99.0}
        report = validate_application(slots)
        assert any(
            err.startswith("eco_surface_exceeds_parcel:") for err in report["errors"]
        )

    def test_missing_optional_fields_are_only_warnings(self):
        slots = dict(VALID_SLOTS)
        schema = load_cap_slots()[0]
        optional = next(name for name, spec in schema.items() if not spec["required"])
        slots.pop(optional, None)
        report = validate_application(slots)
        assert report["valid"] is True
        assert f"missing_optional:{optional}" in report["warnings"]


# --------------------------------------------------------------------------- #
# Form mapping
# --------------------------------------------------------------------------- #
class TestFormMapping:
    def test_mapping_is_tagged_with_schema_version(self):
        _, version = load_cap_slots()
        assert build_form_mapping(VALID_SLOTS)["schema_version"] == version

    def test_beneficiary_is_nested(self):
        beneficiary = build_form_mapping(VALID_SLOTS)["beneficiary"]
        assert beneficiary["nif_cif"] == "12345678Z"
        assert beneficiary["full_name"] == "Ana Ruiz"

    def test_parcel_and_eco_scheme_lists_are_projected(self):
        mapping = build_form_mapping(VALID_SLOTS)
        assert mapping["parcels"][0]["parcel_id"] == "26002A001000010000EQ"
        assert mapping["eco_schemes"][0]["practice_code"] == "AG-ECO-01"

    def test_partial_mapping_omits_absent_sections(self):
        mapping = build_form_mapping({"beneficiary.nif_cif": "12345678Z"})
        assert mapping["beneficiary"] == {"nif_cif": "12345678Z"}
        assert mapping["parcels"] == []
        assert mapping["total_declared_ha"] is None

    def test_values_are_echoed_not_computed(self):
        mapping = build_form_mapping(VALID_SLOTS)
        assert mapping["parcels"][0]["declared_surface_ha"] == 4.2


# --------------------------------------------------------------------------- #
# Amount reproduction
# --------------------------------------------------------------------------- #
class TestEstimatedAmounts:
    RATES = {"unit_rate_eur_ha": "120,50", "practice_rate_eur_ha": 80}

    # 4.2 ha x 120.50 EUR/ha = 506.10 EUR base; 2.0 ha x 80 EUR/ha = 160.00 EUR eco.

    def test_no_rates_produces_no_eur_figures(self):
        amounts = estimated_amounts(VALID_SLOTS, None)
        assert amounts["total_declared_ha"] == 4.2
        assert "estimated_base_eur" not in amounts
        assert "estimated_total_eur" not in amounts

    def test_base_amount_is_reproduced(self):
        amounts = estimated_amounts(VALID_SLOTS, self.RATES)
        assert amounts["estimated_base_eur"] == pytest.approx(506.1)

    def test_eco_amount_uses_applied_surface(self):
        amounts = estimated_amounts(VALID_SLOTS, self.RATES)
        # 2.0 ha applied at 80 EUR/ha, not the 4.2 ha parcel surface.
        assert amounts["estimated_eco_scheme_eur"] == pytest.approx(160.0)

    def test_total_is_the_sum_of_both_lines(self):
        amounts = estimated_amounts(VALID_SLOTS, self.RATES)
        assert amounts["estimated_total_eur"] == pytest.approx(666.1)

    def test_eco_line_falls_back_to_parcel_surface(self):
        slots = {**VALID_SLOTS}
        slots.pop("eco_schemes[].applied_surface_ha")
        amounts = estimated_amounts(slots, self.RATES)
        assert amounts["estimated_eco_scheme_eur"] == pytest.approx(336.0)

    def test_amounts_are_deterministic(self):
        assert estimated_amounts(VALID_SLOTS, self.RATES) == estimated_amounts(
            VALID_SLOTS, self.RATES
        )

    def test_empty_slots_produce_no_eur_figures(self):
        assert "estimated_base_eur" not in estimated_amounts({}, self.RATES)


class TestLoadCapRates:
    """The shipped rate asset must never imply a rate that was not published."""

    def test_unpublished_rates_are_absent_from_the_table(self):
        rates = load_cap_rates()
        # The reference documents give no flat unit/practice figure, so the
        # asset leaves them null and the loader must drop them entirely.
        assert "unit_rate_eur_ha" not in rates
        assert "practice_rate_eur_ha" not in rates

    def test_published_rate_is_loaded(self):
        assert load_cap_rates()["multiannual_bonus_eur_ha"] == pytest.approx(25.0)

    def test_load_only_returns_numeric_rate_keys(self):
        assert all(isinstance(value, float) for value in load_cap_rates().values())

    def test_rates_are_read_only(self):
        rates = load_cap_rates()
        with pytest.raises(TypeError):
            rates["unit_rate_eur_ha"] = 999.0

    def test_asset_rates_do_not_fabricate_amounts(self):
        # A complete application with the shipped asset must report no base or
        # eco-scheme figure, because no such rate is published.
        amounts = estimated_amounts(VALID_SLOTS, load_cap_rates())
        assert "estimated_base_eur" not in amounts
        assert "estimated_eco_scheme_eur" not in amounts
