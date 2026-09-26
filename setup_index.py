import os

from pinecone import Pinecone, ServerlessSpec

from config import (
    EMBEDDING_MODEL,
    INDEX_NAME,
    NAMESPACE,
    PINECONE_CLOUD,
    PINECONE_REGION,
    require_env,
)


def pinecone_client() -> Pinecone:
    require_env("PINECONE_API_KEY")
    return Pinecone(api_key=os.environ["PINECONE_API_KEY"])


def _dimension(description) -> int | None:
    dimension = getattr(description, "dimension", None)
    if dimension is None and isinstance(description, dict):
        dimension = description.get("dimension")
    return dimension


def _create_index(pc: Pinecone, dimension: int) -> None:
    print(
        f"Creando índice '{INDEX_NAME}' "
        f"({dimension} dims, {PINECONE_CLOUD}/{PINECONE_REGION})..."
    )
    pc.create_index(
        name=INDEX_NAME,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
    )


def ensure_index(dimension: int) -> str:
    """Crea el índice serverless si no existe y alinea la dimensión del encoder."""
    pc = pinecone_client()
    names = pc.list_indexes().names()

    if INDEX_NAME in names:
        current = _dimension(pc.describe_index(INDEX_NAME))
        if current != dimension:
            print(
                f"El índice '{INDEX_NAME}' tiene {current} dims y "
                f"{EMBEDDING_MODEL} genera {dimension}. Se recrea."
            )
            pc.delete_index(INDEX_NAME)
            names = []
        else:
            print(f"El índice '{INDEX_NAME}' ya existe.")

    if INDEX_NAME not in names:
        _create_index(pc, dimension)

    description = pc.describe_index(INDEX_NAME)
    created = _dimension(description)
    if created != dimension:
        raise RuntimeError(
            f"El índice '{INDEX_NAME}' quedó en {created} dims, "
            f"pero {EMBEDDING_MODEL} genera {dimension}."
        )

    print(f"Índice listo. Namespace de trabajo: '{NAMESPACE}'.")
    return INDEX_NAME


if __name__ == "__main__":
    from embeddings import get_embeddings

    probe = get_embeddings().embed_query("dimension")
    ensure_index(len(probe))
