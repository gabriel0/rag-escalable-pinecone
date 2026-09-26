import hashlib
import json
import re
from pathlib import Path

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SIZE_TOKENS,
    CHUNKS_PATH,
    DATA_DIR,
)

def read_text(path: Path) -> str:
    raw_bytes = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[\u200b-\u200d\ufeff\u00ad]", "", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_id(doc_id: str, page: int, text: str) -> str:
    payload = f"{doc_id}\n{page}\n{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_documents(data_dir: Path = DATA_DIR) -> list[Document]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de datos: {data_dir}")

    files = sorted(path for path in data_dir.glob("*.md") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No hay archivos .md en {data_dir}")

    tokenizer = tiktoken.get_encoding("cl100k_base")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
        length_function=lambda text: len(tokenizer.encode(text)),
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documents: list[Document] = []
    for path in files:
        doc_id = path.stem
        raw = clean_text(read_text(path))
        if not raw:
            print(f"{path.name}: vacío, se omite")
            continue
        chunks = splitter.split_text(raw)
        category = doc_id
        tags = [doc_id]
        print(f"{path.name}: {len(tokenizer.encode(raw))} tokens -> {len(chunks)} chunks")
        for index, text in enumerate(chunks, start=1):
            identifier = chunk_id(doc_id, index, text)
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "chunk_id": identifier,
                        "doc_id": doc_id,
                        "source": path.name,
                        "page": index,
                        "category": category,
                        "tags": tags,
                    },
                )
            )
    return documents


def save_chunks(documents: list[Document], path: Path = CHUNKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"page_content": doc.page_content, "metadata": doc.metadata}
        for doc in documents
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_chunks(path: Path = CHUNKS_PATH) -> list[Document]:
    if not path.is_file():
        raise FileNotFoundError(
            f"No está {path}. Corré primero: python ingest.py"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        Document(page_content=item["page_content"], metadata=item["metadata"])
        for item in payload
    ]
