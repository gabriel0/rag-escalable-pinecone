import json
import sys

from config import GOLDEN_PATH, TOP_K
from rag import RAGSystem


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top = retrieved[:k]
    hits = sum(1 for doc_id in top if doc_id in relevant)
    return hits / k


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    found = set(retrieved[:k]) & relevant
    return len(found) / len(relevant)


def load_golden(path=GOLDEN_PATH) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"No está el golden set: {path}")
    items = json.loads(path.read_text(encoding="utf-8"))
    if len(items) < 5:
        raise RuntimeError("El golden set debe tener al menos 5 preguntas.")
    return items


def evaluate(k: int = TOP_K) -> dict:
    golden = load_golden()
    system = RAGSystem(k=k)
    rows = []

    print(f"Evaluación BM25 + Pinecone  k={k}")
    print("-" * 72)
    for index, item in enumerate(golden, start=1):
        expected = item["documento_id_esperado"]
        relevant = {expected}
        hits = system.query(item["pregunta"], k=k)
        retrieved = [str(doc.metadata.get("doc_id", "")) for doc in hits]
        precision = precision_at_k(retrieved, relevant, k)
        recall = recall_at_k(retrieved, relevant, k)
        rows.append(
            {
                "pregunta": item["pregunta"],
                "esperado": expected,
                "recuperados": retrieved,
                "precision": precision,
                "recall": recall,
            }
        )
        print(f"{index}. {item['pregunta']}")
        print(f"   esperado: {expected}")
        print(f"   top-{k}: {', '.join(retrieved) if retrieved else '(vacío)'}")
        print(f"   Recall@{k}={recall:.2f}  Precision@{k}={precision:.2f}")

    mean_precision = sum(row["precision"] for row in rows) / len(rows)
    mean_recall = sum(row["recall"] for row in rows) / len(rows)
    print("-" * 72)
    print(f"Promedio Recall@{k}: {mean_recall:.2f}")
    print(f"Promedio Precision@{k}: {mean_precision:.2f}")
    print(
        "Un chunk cuenta como útil si su doc_id coincide con el documento esperado. "
        f"\nRecall@{k} es 1 cuando ese documento aparece al menos una vez.\n"
        f"Precision@{k} es 1 cuando el documento esperado aparece en el top-{k}."
    )
    return {
        "k": k,
        "precision": mean_precision,
        "recall": mean_recall,
        "rows": rows,
    }

if __name__ == "__main__":
    _utf8_stdio()
    evaluate()