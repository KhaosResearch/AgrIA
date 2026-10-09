"""Deterministic helpers for the CAP application workflow.

All form mapping, completeness checks and validation live here so that they can
be unit tested without an LLM. The LLM is only ever allowed to *propose* slot
values; every value that reaches `cap_form_data` passes through this module.
"""

import json
import re
from functools import lru_cache
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any, Iterable, Optional

from ..config.constants import BASE_PROMPTS_PATH

SLOTS_ASSET = "CAP_SLOTS.json"
RATES_ASSET = "CAP_RATES.json"

# ES/EN decimal conventions seen in real parcel assessments.
# A candidate numeric token: digits with , . or space as separators, plus an
# optional trailing decimal part. Deliberately greedy over separators so that
# "1.234,5" and "1,234.5" both survive intact for parse_number to normalise.
_NUMERIC_TOKEN_RE = re.compile(r"\d[\d.,]*\d|\d")
_HA_RE = re.compile(r"(-?\d[\d.,]*)\s*(?:ha\b|hect)", re.IGNORECASE)


@lru_cache(maxsize=1)
def load_cap_slots() -> tuple[dict[str, dict], str]:
    """Return (slots_by_name, schema_version) for the CAP slot schema."""
    path = BASE_PROMPTS_PATH / SLOTS_ASSET
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    slots = {slot["name"]: slot for slot in payload["slots"]}
    return slots, payload.get("schema_version", "0.0.0")


@lru_cache(maxsize=1)
def _load_cap_rates() -> Mapping[str, float]:
    """Read the explicit EUR/ha rate table from the versioned asset.

    Entries left `null` in the asset are dropped, so a rate that has not been
    published can never be mistaken for a real one and silently inflate an
    amount.
    """
    path = BASE_PROMPTS_PATH / RATES_ASSET
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return MappingProxyType(
        {
            key: float(value)
            for key, value in (payload.get("rates") or {}).items()
            if value is not None
        }
    )


def load_cap_rates() -> Mapping[str, float]:
    """Return the campaign's explicit EUR/ha rates as a read-only mapping.

    The result is cached, so callers must not be able to mutate the shared
    table: a single stray assignment would otherwise change every later
    amount the agent reports.
    """
    return _load_cap_rates()


def slot_definition(name: str) -> Optional[dict]:
    """Return the schema definition for a slot, or None when unknown."""
    return load_cap_slots()[0].get(name)


def is_valid_slot(name: str) -> bool:
    """Whether `name` belongs to the schema (LLM output is gated on this)."""
    return name in load_cap_slots()[0]


def coerce_value(name: str, value: Any) -> Any:
    """Normalise a proposed value to the slot's declared type.

    Numbers are parsed from both `1.234,5` (ES) and `1,234.5` (EN) notation;
    unknown slots or unparseable values return None so the caller can reject.
    """
    spec = slot_definition(name)
    if spec is None or value is None:
        return None

    if spec["type"] == "number":
        parsed = parse_number(value)
        return parsed if parsed is not None else None

    if spec["type"] == "array":
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if str(v).strip()]
        return [part.strip() for part in str(value).split(",") if part.strip()]

    text = str(value).strip()
    if not text:
        return None

    allowed = spec.get("enum")
    if allowed and text not in allowed:
        # Accept loose input such as "regadio " or "de regadio".
        lowered = text.lower()
        for option in allowed:
            if option.lower() in lowered:
                return option
        return None
    return text


def _normalize_numeric_token(token: str) -> Optional[float]:
    """Turn a separator-laden numeric token into a float.

    Rules (applied in order, so ES and EN notation both work):
      1. strip spaces and stray percent signs;
      2. both separators present -> the *last* one is the decimal mark and the
         other groups thousands ("1.234,56" and "12,345.67" both parse correctly);
      3. one separator present -> decimal mark only when it is not followed by
         exactly three digits (that shape is a thousands group: "1,500");
      4. repeated separators -> the last one is the decimal mark, the rest group.
    """
    raw = token.strip().replace(" ", "").replace("%", "")
    if not raw:
        return None

    has_comma, has_dot = "," in raw, "." in raw
    if has_comma and has_dot:
        decimal_sep = "," if raw.rfind(",") > raw.rfind(".") else "."
        thousands_sep = "." if decimal_sep == "," else ","
        raw = raw.replace(thousands_sep, "").replace(decimal_sep, ".")
    else:
        sep = "," if has_comma else ("." if has_dot else None)
        if sep is not None:
            head, _, tail = raw.rpartition(sep)
            is_decimal = tail != "" and len(tail) != 3
            # Grouping shape keeps the tail digits; decimal shape keeps the mark.
            raw = head.replace(sep, "") + (("." + tail) if is_decimal else tail)

    try:
        return float(raw)
    except ValueError:
        return None


def parse_number(value: Any) -> Optional[float]:
    """Best-effort numeric parse across ES/EN thousands and decimal marks."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value)
    # Prefer an explicit "<number> ha" match: it ignores parcel IDs like "26002A001".
    ha_match = _HA_RE.search(text)
    if ha_match:
        return _normalize_numeric_token(ha_match.group(1))

    token_match = _NUMERIC_TOKEN_RE.search(text)
    if not token_match:
        return None
    return _normalize_numeric_token(token_match.group(0))


def normalise_slots(proposed: Optional[dict]) -> dict[str, Any]:
    """Filter an LLM-proposed slot dict down to known, coercible entries."""
    if not isinstance(proposed, dict):
        return {}

    accepted: dict[str, Any] = {}
    for name, value in proposed.items():
        if not is_valid_slot(name):
            continue  # never invent fields outside the schema
        coerced = coerce_value(name, value)
        if coerced is not None:
            accepted[name] = coerced
    return accepted


def merge_slots(existing: Optional[dict], incoming: Optional[dict]) -> dict[str, Any]:
    """Merge accepted slots over existing ones, dropping empty values."""
    merged = dict(existing or {})
    for name, value in (incoming or {}).items():
        if value is None or value == "" or value == []:
            continue  # an unanswered question must not clear a prior value
        merged[name] = value
    return merged


def _has_value(value: Any) -> bool:
    return value is not None and value != "" and value != []


def missing_required_slots(slots: Optional[dict]) -> list[str]:
    """Names of required slots that have no usable value yet."""
    schema = load_cap_slots()[0]
    data = slots or {}
    return [
        name
        for name, spec in schema.items()
        if spec["required"] and not _has_value(data.get(name))
    ]


def missing_slot_descriptions(lang: str = "es") -> list[dict]:
    """Bilingual question specs for every required slot, schema order."""
    schema = load_cap_slots()[0]
    key = "question_en" if lang == "en" else "question_es"
    return [
        {"name": name, "question": spec[key]}
        for name, spec in schema.items()
        if spec["required"]
    ]


def first_missing_slot(slots: Optional[dict], lang: str = "es") -> Optional[dict]:
    """The single next slot to ask about, or None when collection is complete."""
    schema = load_cap_slots()[0]
    data = slots or {}
    key = "question_en" if lang == "en" else "question_es"
    for name, spec in schema.items():
        if spec["required"] and not _has_value(data.get(name)):
            return {"name": name, "question": spec[key]}
    return None


def validate_application(slots: Optional[dict]) -> dict[str, Any]:
    """Deterministic validation of a CAP application.

    Returns a report with `valid`, `missing_required`, `errors` and `warnings`.
    `errors` covers values that are present but unusable (bad enum, unparseable
    number); `warnings` covers soft issues such as missing optional fields.
    """
    schema = load_cap_slots()[0]
    data = slots or {}
    errors: list[str] = []
    warnings: list[str] = []

    for name, spec in schema.items():
        value = data.get(name)
        if not _has_value(value):
            if spec["required"]:
                errors.append(f"missing_required:{name}")
            continue

        if spec["type"] == "number" and not isinstance(value, (int, float)):
            errors.append(f"invalid_type:{name}")
        if spec.get("enum") and value not in spec["enum"]:
            errors.append(f"invalid_value:{name}={value}")

    # Cross-field check: eco-scheme surface cannot exceed the declared parcel area.
    declared = parse_number(data.get("parcels[].declared_surface_ha"))
    applied = parse_number(data.get("eco_schemes[].applied_surface_ha"))
    if declared is not None and applied is not None and applied > declared:
        errors.append(f"eco_surface_exceeds_parcel:{applied}>{declared}")

    for name, spec in schema.items():
        if not spec["required"] and not _has_value(data.get(name)):
            warnings.append(f"missing_optional:{name}")

    return {
        "valid": not errors,
        "missing_required": [
            e.split(":", 1)[1] for e in errors if e.startswith("missing_required")
        ],
        "errors": errors,
        "warnings": warnings,
    }


def build_form_mapping(slots: Optional[dict]) -> dict[str, Any]:
    """Project collected slots onto the versioned CAP application structure.

    Values are echoed verbatim; nothing is computed or invented here.
    """
    schema, version = load_cap_slots()
    data = slots or {}

    beneficiary = {
        key.split(".", 1)[1]: data[key]
        for key in ("beneficiary.nif_cif", "beneficiary.full_name", "beneficiary.iban")
        if _has_value(data.get(key))
    }

    parcels: list[dict] = []
    parcel_keys = [k for k in schema if k.startswith("parcels[].")]
    if any(_has_value(data.get(k)) for k in parcel_keys):
        parcels = [
            {
                "parcel_id": data.get("parcels[].parcel_id"),
                "declared_crop": data.get("parcels[].declared_crop"),
                "declared_surface_ha": data.get("parcels[].declared_surface_ha"),
                "irrigation_type": data.get("parcels[].irrigation_type"),
            }
        ]

    eco_schemes: list[dict] = []
    if _has_value(data.get("eco_schemes[].practice_code")):
        eco_schemes = [
            {
                "practice_code": data.get("eco_schemes[].practice_code"),
                "applied_surface_ha": data.get("eco_schemes[].applied_surface_ha"),
            }
        ]

    total_ha = parse_number(data.get("parcels[].declared_surface_ha"))
    return {
        "schema_version": version,
        "beneficiary": beneficiary or None,
        "requested_aid_lines": data.get("requested_aid_lines") or [],
        "parcels": parcels,
        "eco_schemes": eco_schemes,
        "total_declared_ha": total_ha,
    }


def estimated_amounts(
    slots: Optional[dict], rates: Optional[dict] = None
) -> dict[str, Any]:
    """Reproduce estimated amounts from a supplied rate table.

    The rate table is passed in (never guessed) so that any figure the agent
    reports is reproducible from state plus explicit rates.
    """
    data = slots or {}
    table = rates or {}
    total_ha = parse_number(data.get("parcels[].declared_surface_ha"))
    unit_rate = parse_number(table.get("unit_rate_eur_ha"))
    practice_rate = parse_number(table.get("practice_rate_eur_ha"))

    amounts: dict[str, Any] = {"total_declared_ha": total_ha}
    if total_ha is not None and unit_rate is not None:
        amounts["estimated_base_eur"] = round(total_ha * unit_rate, 2)
    if total_ha is not None and practice_rate is not None:
        applied = parse_number(data.get("eco_schemes[].applied_surface_ha")) or total_ha
        amounts["estimated_eco_scheme_eur"] = round(applied * practice_rate, 2)
        if "estimated_base_eur" in amounts:
            amounts["estimated_total_eur"] = round(
                amounts["estimated_base_eur"] + amounts["estimated_eco_scheme_eur"], 2
            )
    return amounts


def collect_field_names(slots: Optional[dict]) -> Iterable[str]:
    """Iterate the slot names carrying a value."""
    return (name for name, value in (slots or {}).items() if _has_value(value))
