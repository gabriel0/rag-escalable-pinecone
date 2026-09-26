from langchain_pinecone import PineconeVectorStore

from config import INDEX_NAME, NAMESPACE
from chunks import build_documents, save_chunks
from embeddings import get_embeddings
from setup_index import ensure_index, pinecone_client


def clear_namespace() -> None:
    index = pinecone_client().Index(INDEX_NAME)
    try:
        index.delete(delete_all=True, namespace=NAMESPACE)
        print(f"Namespace '{NAMESPACE}' vaciado.")
    except Exception as exc:
        message = str(exc).lower()
        if "namespace not found" in message or "404" in message:
            print(f"Namespace '{NAMESPACE}' todavía no tenía vectores.")
            return
        raise


def ingest() -> int:
    encoder = get_embeddings()
    ensure_index(len(encoder.embed_query("dimension")))
    documents = build_documents()
    if not documents:
        raise RuntimeError("El corpus no produjo chunks.")

    clear_namespace()
    ids = [doc.metadata["chunk_id"] for doc in documents]
    PineconeVectorStore.from_documents(
        documents=documents,
        embedding=encoder,
        index_name=INDEX_NAME,
        namespace=NAMESPACE,
        ids=ids,
    )
    save_chunks(documents)
    print(
        f"Upsert listo: {len(documents)} chunks en "
        f"'{INDEX_NAME}' / namespace '{NAMESPACE}'."
    )
    print("El texto de cada chunk quedó en la metadata (campo text).")
    return len(documents)


if __name__ == "__main__":
    ingest()
