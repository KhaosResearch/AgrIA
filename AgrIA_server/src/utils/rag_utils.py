import chromadb
import hashlib
import structlog

from chromadb.utils import embedding_functions
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from typing import List

from ..config.constants import BASE_CONTEXT_PATH, COLLECTION_NAME, VECTOR_DB_PATH

logger = structlog.get_logger(__name__)


def get_embedding_function():
    """Returns standard default embedding model (onnx/all-MiniLM-L6-v2) running locally."""
    return embedding_functions.DefaultEmbeddingFunction()


def chunk_document(
    file_path: Path, chunk_size: int = 800, chunk_overlap: int = 150
) -> List:
    """
    Reads a PDF or Markdown document and yields smaller, overlapping text segments.
    """
    logger.info(f"📖 Loading document for chunking: {file_path.name}")
    if file_path.suffix.lower() == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif file_path.suffix.lower() in [".md", ".txt", ".json"]:
        loader = TextLoader(str(file_path), encoding="utf-8")
    else:
        logger.warning(f"Unsupported file format skipped: {file_path.name}")
        return []

    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"✂️ Generated {len(chunks)} chunks from {file_path.name}")
    return chunks


def add_documents_to_kb(collection, document_paths: List[Path]):
    """
    Processes a list of document file paths, generates embeddings, and adds them to ChromaDB.
    """
    raw_texts = []
    metadatas = []
    ids = []

    for file_path in document_paths:
        if not file_path.exists() or file_path.name.startswith("_"):
            continue
        chunks = chunk_document(file_path)
        for idx, chunk in enumerate(chunks):
            content = chunk.page_content.strip()
            if not content:
                continue

            # Deterministic ID based on file content and index
            chunk_id = hashlib.md5(
                f"{file_path.name}_{idx}_{content[:30]}".encode()
            ).hexdigest()

            raw_texts.append(content)

            meta = {"source_file": file_path.name, "chunk_index": idx}
            if hasattr(chunk, "metadata") and chunk.metadata:
                # Merge page numbers if extracted by PyPDFLoader
                if "page" in chunk.metadata:
                    meta["page_number"] = chunk.metadata["page"]

            metadatas.append(meta)
            ids.append(chunk_id)

    if raw_texts:
        logger.info(f"💾 Adding {len(raw_texts)} vector embeddings to ChromaDB...")
        collection.add(documents=raw_texts, metadatas=metadatas, ids=ids)
        logger.info("✅ Vector database ingestion complete.")
    else:
        logger.info("No new valid text chunks found to add.")


def get_or_create_knowledge_base(
    collection_name: str = COLLECTION_NAME,
    base_files_dir: Path | str = BASE_CONTEXT_PATH / "files",
    reset_database: bool = False,
):
    """
    Initializes ChromaDB persistent client. Creates or loads the CAP knowledge base collection.
    """
    logger.info("📦 Connecting to ChromaDB persistent store...")

    chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    embedding_fn = get_embedding_function()

    if reset_database:
        try:
            chroma_client.delete_collection(name=collection_name)
            logger.info("🗑️ Existing collection reset requested and purged.")
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name, embedding_function=embedding_fn
    )

    existing_count = collection.count()
    if existing_count > 0 and not reset_database:
        logger.info(
            f"💾 Found existing knowledge base with {existing_count} vector chunks."
        )
        return collection

    # Auto-populate if empty
    logger.info(f"🚀 Collection is empty. Ingesting PDF files from {base_files_dir}...")
    files_to_ingest = (
        list(base_files_dir.glob("*.pdf"))
        + list(base_files_dir.glob("*.md"))
        + list(base_files_dir.glob("*.txt"))
        + list(base_files_dir.glob("*.json"))
    )
    # if not files_to_ingest or len(files_to_ingest) < 1:
    # logger.info("No PDF files found. Searching for MD and TXT files...")
    # files_to_ingest = list(base_files_dir.glob("*.md")) + list(
    #     base_files_dir.glob("*.txt")
    # )
    add_documents_to_kb(collection, files_to_ingest)

    return collection


def query_knowledge_base(collection, query_text: str, n_results: int = 3) -> str:
    """
    Performs vector similarity search and returns concatenated top matching passages.
    """
    results = collection.query(query_texts=[query_text], n_results=n_results)

    retrieved_documents = results.get("documents", [[]])[0]
    retrieved_metadatas = results.get("metadatas", [[]])[0]

    formatted_context = []
    for doc, meta in zip(retrieved_documents, retrieved_metadatas):
        src = meta.get("source_file", "Unknown")
        page = f" (Page {meta['page_number']})" if "page_number" in meta else ""
        formatted_context.append(f"--- FROM: {src}{page} ---\n{doc}")
    with open("rag.log", "w") as f:
        f.write("\n\n".join(formatted_context))
    return "\n\n".join(formatted_context)
