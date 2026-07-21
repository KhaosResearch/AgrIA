import structlog

from pypdf import PdfReader
from ..config.constants import BASE_CONTEXT_PATH

logger = structlog.get_logger(__file__)

CACHE_FILE = BASE_CONTEXT_PATH / "_cached_regulatory_context.txt"


def load_cached_regulatory_context() -> str:
    """
    Reads all PDF context files from BASE_CONTEXT_PATH using pypdf,
    extracts their text content, and caches it to a single file for JIT node injection.
    """
    # 1. Return cached file if it already exists
    if CACHE_FILE.exists():
        return CACHE_FILE.read_text(encoding="utf-8")

    pdf_files = list(BASE_CONTEXT_PATH.glob("*.pdf"))

    # Fallback to .md or .txt files if no PDFs are found in the directory
    if not pdf_files:
        text_files = list(BASE_CONTEXT_PATH.glob("*.md")) + list(
            BASE_CONTEXT_PATH.glob("*.txt")
        )
        combined_text = "\n\n".join(
            [f.read_text(encoding="utf-8") for f in text_files if f != CACHE_FILE]
        )
        return combined_text

    extracted_blocks = []
    logger.debug(f"[pypdf Loader] Processing {len(pdf_files)} PDF context documents...")

    # 2. Iterate through PDF documents and extract text page by page
    for pdf_path in pdf_files:
        try:
            reader = PdfReader(str(pdf_path))
            pdf_text = f"=== DOCUMENT: {pdf_path.name} ===\n"

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n"

            extracted_blocks.append(pdf_text)
        except Exception as e:
            logger.error(
                f"[pypdf Loader] Warning: Failed to extract {pdf_path.name}: {e}"
            )

    full_context = "\n\n".join(extracted_blocks)

    # 3. Cache the merged output for instant future execution
    if full_context.strip():
        CACHE_FILE.write_text(full_context, encoding="utf-8")

    return full_context
