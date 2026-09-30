import asyncio
import json
import os
import pymupdf
import pymupdf4llm
import structlog

from pathlib import Path

from ..config.constants import CAP_FORMS_PATH, SENSITIVE_INFO_FORM_FIELD_NAMES
from ..config.llm_client import client

logger = structlog.get_logger(__name__)

SYS_INS = """
You are a precise data extraction engine. You will be provided with document text in Markdown format and a target list of sensitive form fields.

Instructions:
1. Locate every instance of the requested form fields in the document, even if the same field name appears multiple times for different entities (e.g., Owner, Representative, Spouse).
2. For every extracted field, identify its context/entity role from the form section header (e.g., "Solicitante", "Representante", "Cónyuge", "General").
3. Extract the exact character string as it appears in the Markdown without modifying, reformatting, or standardizing it.
4. If a value is split across lines or cells, capture the exact raw string.

Reply with only the JSON output and nothing else.

<example_input>Get these fields: ["CIF/NIF", "Nombre", "Email"]</example_input>
<example_output>
{
  "extracted_sensitive_values": [
    {
      "field_name": "CIF/NIF",
      "entity_role": "Solicitante",
      "extracted_value": "52588373T"
    },
    {
      "field_name": "CIF/NIF",
      "entity_role": "Cónyuge",
      "extracted_value": "74907672F"
    },
    {
      "field_name": "Email",
      "entity_role": "Solicitante",
      "extracted_value": "juangarhur@gmail.com"
    }
  ]
}
</example_output>
"""


def anonymize_pdf(
    input_path: str | Path,
    output_path: str | Path,
    redact_terms: list[str] | None = None,
) -> None:
    """
    Create an anonymized copy of a PDF by permanently redacting
    all occurrences of the supplied terms.

    If redact_terms is not provided, SENSITIVE_INFO_FORM_FIELD_NAMES
    is used.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    terms = (
        redact_terms if redact_terms is not None else SENSITIVE_INFO_FORM_FIELD_NAMES
    )

    doc = pymupdf.open(input_path)

    try:
        for page in doc:
            for term in terms:
                areas = page.search_for(term)
                if areas:
                    for area in areas:
                        page.add_redact_annot(
                            area,
                            fill=(0, 0, 0),
                        )

            # Permanently remove the redacted content.
            page.apply_redactions()

        doc.save(output_path)

    finally:
        doc.close()


def _parse_llm_dict(content: str) -> dict:
    content = content.strip()

    # Handle ```json ... ``` or ``` ... ```
    if content.startswith("```"):
        lines = content.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    # First try real JSON
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fall back to Python dict syntax
        import ast

        result = ast.literal_eval(content)

    if not isinstance(result, dict):
        raise ValueError(f"Expected a dict, got {type(result).__name__}: {content!r}")

    return result


def redact_sensitive_data_from_pdf(
    in_file: str | Path,
    out_file: str | Path = "",
    field_names: list[str] = SENSITIVE_INFO_FORM_FIELD_NAMES,
) -> None:
    """
    PDF data redaction pipeline for sensitive and personal CAP form data fields (including address and bank details).
    Takes the file and a list of field names and uses and parses from PDF to MD format.
    An LLM then detects and extract a list of the field values on the MD file.
    The PDF filepath and the extracted values list are then passed to the `anonymize_pdf` to redact those specific terms from the document.

    Args:
        in_file (str): Input file path.
        out_file (str, optional): Output file path. By default, saves the output to the `CAP_FORMS_PATH` dir with the `in_file` basename and the `"_redacted"` tag.
        field_names (list[str], optional): List of all field names with sensitive data. By defautl, is `SENSITIVE_INFO_FORM_FIELD_NAMES`.
    """
    # Open PDF and parse to MD
    doc = pymupdf.open(in_file)
    logger.debug(f"Document's total pages: {doc.page_count}")
    md_text = pymupdf4llm.to_markdown(in_file)
    text_data = f"This is the relevant text:\nSTART\n{md_text}\nEND"

    # Compose LLM input for term list extraction
    human_msg = f"Locate all of the sensitive data terms, like personal data, address and bank information and extract them from the text. Use these terms to locate the fields on the text: {field_names}"

    msg = [
        ("system", SYS_INS),
        ("human", f"{human_msg + '\n' + text_data}"),
    ]
    summary_method = getattr(client, "ainvoke", None)
    if summary_method is not None:
        llm_response = asyncio.run(summary_method(msg))
    else:
        llm_response = client.invoke(msg)

    response_dict = _parse_llm_dict(llm_response.content)

    # Get terms to redact and remove them from PDF
    terms_to_redact = list(
        dict.fromkeys(
            item["extracted_value"]
            for item in response_dict["extracted_sensitive_values"]
            if item["extracted_value"] not in (None, "null")
        )
    )
    logger.debug(f"All sensitive data found: {terms_to_redact}")

    # Sort out_file value
    if out_file == "":
        filename, ext = os.path.splitext(os.path.basename(in_file))
        out_file = str(CAP_FORMS_PATH / f"{filename}_redacted{ext}")
    anonymize_pdf(in_file, out_file, terms_to_redact)
    logger.info(f"All data saved to:\n\t{out_file}")


if "__main__" == __name__:
    in_file = str("path" / "to" / "cap_form.pdf")
    out_file = str(CAP_FORMS_PATH / "cap_form_redacted.pdf")
    redact_sensitive_data_from_pdf(in_file=in_file, out_file=out_file)
