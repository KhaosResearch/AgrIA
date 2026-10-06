import asyncio
import json
import pdfplumber

from pathlib import Path

from ..config.llm_client import client
from ..models.cap_form_models import CAPFullApplicationSchema


SYS_INS = """You are an expert system processing Spanish CAP (Solicitud Única) documents.
Extract all relevant application details into the requested JSON structure according to the target schema.
If personal identifiers are missing or redacted, use null for those fields while preserving parcel, crop, and aid data."""


def extract_pdf_text(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
    return full_text


def process_cap_document(
    client, pdf_path: str, human_msg: str = "Extract all fields from this CAP document:"
):
    # 1. Parse raw text from PDF
    text_data = extract_pdf_text(pdf_path)

    # 2. Attach schema enforcement to local client if using LangChain wrapper
    client = client.with_structured_output(CAPFullApplicationSchema)

    # 3. Format payload using local LLM invocation syntax
    msg = [
        ("system", SYS_INS),
        ("human", f"{human_msg + '\n' + text_data}"),
    ]

    # 4. Invoke LLM using client's execution model
    summary_method = getattr(client, "ainvoke", None)
    if summary_method is not None:
        llm_response = asyncio.run(summary_method(msg))
    else:
        llm_response = client.invoke(msg)

    response = llm_response

    # Handle different response types gracefully
    if isinstance(response, CAPFullApplicationSchema):
        output_data = response.model_dump_json(indent=4, warnings=False)
    elif isinstance(response, dict):
        output_data = json.dumps(response, indent=4)
    else:
        # Fallback for objects with __dict__ or arbitrary responses
        try:
            output_data = json.dumps(response.__dict__, indent=4)
        except Exception:
            output_data = json.dumps(
                {
                    "error": "Could not serialize response",
                    "type": type(response).__name__,
                    "str_representation": str(response),
                },
                indent=4,
            )

    return output_data


if __name__ == "__main__":
    out_path = "schema_response.json"
    # pdf_path = "/home/miguel/Dev/AgrIA/misc/pdf/JOSE MANUEL GARCIA NIETO2024.pdf"
    pdf_path = "/home/miguel/Dev/AgrIA/AgrIA_server/assets/LLM_assets/context/forms/cap_form_redacted_JM.pdf"

    response = process_cap_document(
        client=client,
        pdf_path=pdf_path,
    )
    Path(out_path).write_text(
        response,
        encoding="utf-8",
    )
    print(f"All saved to {out_path}")
