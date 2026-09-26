import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
ARTIFACTS_DIR = ROOT / "artifacts"
CHUNKS_PATH = ARTIFACTS_DIR / "chunks.json"
GOLDEN_PATH = ROOT / "eval" / "golden_set.json"

INDEX_NAME = os.getenv("INDEX_NAME")
NAMESPACE = os.getenv("PINECONE_NAMESPACE")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL").strip().rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL").strip()
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    {
        "openai": "text-embedding-3-small",
        "google": "gemini-embedding-001",
        "ollama": OLLAMA_EMBED_MODEL,
    }.get(EMBEDDING_PROVIDER, OLLAMA_EMBED_MODEL),
)
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"

CHUNK_SIZE_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 80
TOP_K = 5

# Pesos del EnsembleRetriever: lexico (BM25) y denso (Pinecone).
BM25_WEIGHT = 0.5
DENSE_WEIGHT = 0.5

def require_env(*names: str) -> None:
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Faltan variables en .env: {joined}. "
            "Copia .env.example a .env y completa las claves."
        )
