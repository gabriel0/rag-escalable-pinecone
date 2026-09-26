import argparse
import re
import sys
import unicodedata
from collections.abc import Callable, Iterable

from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_pinecone import PineconeVectorStore
from pydantic import ConfigDict, Field
from rank_bm25 import BM25Okapi

from config import (
    BM25_WEIGHT,
    DENSE_WEIGHT,
    INDEX_NAME,
    NAMESPACE,
    TOP_K,
    require_env,
)
from chunks import load_chunks
from embeddings import get_embeddings


def tokenize(text: str) -> list[str]:
    """Parte identificadores (k8sFunctions.getVersionDeploy) y quita acentos."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    normalized = unicodedata.normalize("NFD", spaced)
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return re.findall(r"[a-z0-9]+", without_accents.lower())


class BM25Retriever(BaseRetriever):
    """BM25 local sobre rank_bm25. No depende de langchain-community."""

    vectorizer: BM25Okapi
    docs: list[Document] = Field(repr=False)
    k: int = 4
    preprocess_func: Callable[[str], list[str]]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[Document],
        *,
        k: int = 4,
        preprocess_func: Callable[[str], list[str]] = tokenize,
    ) -> "BM25Retriever":
        docs = list(documents)
        vectorizer = BM25Okapi([preprocess_func(doc.page_content) for doc in docs])
        return cls(vectorizer=vectorizer, docs=docs, k=k, preprocess_func=preprocess_func)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        processed = self.preprocess_func(query)
        return list(self.vectorizer.get_top_n(processed, self.docs, n=self.k))


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


class RAGSystem:
    """Recuperador híbrido: BM25 local + similitud en Pinecone."""

    def __init__(self, documents: list[Document] | None = None, k: int = TOP_K):
        require_env("PINECONE_API_KEY")
        self.k = k
        self.documents = documents if documents is not None else load_chunks()
        if not self.documents:
            raise RuntimeError("No hay chunks para armar el recuperador.")

        embeddings = get_embeddings()
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=NAMESPACE,
        )
        # Cada lista trae más candidatos; query() se queda con el top final.
        candidate_k = max(k * 2, 10)
        self.bm25 = BM25Retriever.from_documents(
            self.documents, k=candidate_k, preprocess_func=tokenize
        )
        self.dense = vectorstore.as_retriever(
            search_kwargs={"k": candidate_k, "namespace": NAMESPACE}
        )
        self.ensemble = EnsembleRetriever(
            retrievers=[self.bm25, self.dense],
            weights=[BM25_WEIGHT, DENSE_WEIGHT],
            id_key="chunk_id",
        )

    def query(self, consulta: str, k: int | None = None) -> list[Document]:
        limit = self.k if k is None else k
        return self.ensemble.invoke(consulta)[:limit]


def _print_hits(documents: list[Document]) -> None:
    if not documents:
        print("Sin resultados.")
        return
    for rank, doc in enumerate(documents, start=1):
        meta = doc.metadata
        preview = " ".join(doc.page_content.split())[:180]
        print(
            f"{rank}. doc_id={meta.get('doc_id')} "
            f"source={meta.get('source')} page={meta.get('page')} "
            f"category={meta.get('category')}"
        )
        print(f"   {preview}")


def main() -> None:
    _utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Consulta el recuperador híbrido (BM25 + Pinecone)."
    )
    parser.add_argument("consulta", help="Pregunta a recuperar")
    args = parser.parse_args()
    hits = RAGSystem().query(args.consulta)
    _print_hits(hits)


if __name__ == "__main__":
    main()
