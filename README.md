# Pre-entrega 4: RAG escalable en Pinecone

Servicio de recuperación híbrida. Indexa la documentación de la librería en un
índice **Pinecone Serverless**, busca con similitud de vectores y con BM25, y
mide Precision@5 y Recall@5 contra un golden set.

El texto de cada chunk queda en la metadata del vector (campo `text`). No hace
falta una base relacional para reconstruir el fragmento.

## Chunks, overlap y embeddings

Un **chunk** es un pedazo de un markdown. Los archivos de `data/` son largos
para compararlos enteros contra una pregunta, así que `chunks.py` los corta en
trozos de 600 tokens. Cada trozo guarda el nombre del archivo (`doc_id`), el
número de trozo (`page`, empieza en 1) y el texto.

El **overlap** es la parte que se repite entre un trozo y el siguiente. Acá son
80 tokens. Si el corte cae en el medio de `installHelmChart`, el chunk de
atrás termina con el inicio del método y el de adelante vuelve a incluir ese
mismo inicio. Así la explicación no queda partida en dos resultados que, por
separado, no alcanzan.

Un **embedding** es la lista de números que representa ese texto. Ollama, con
`all-minilm`, convierte cada chunk en un vector de 384 números. Dos textos que
hablan de lo mismo quedan con vectores parecidos, aunque no usen las mismas
palabras. Pinecone no guarda el modelo: guarda esos números, y al lado el texto
original en la metadata.

Las tres cosas se usan en este orden:

1. `chunks.py` lee `data/`, corta con overlap y arma la lista de chunks.
2. `embeddings.py` pasa cada chunk por `all-minilm` y obtiene su vector.
3. `ingest.py` sube a Pinecone el vector junto con el texto y la metadata, y
   deja la misma lista en `artifacts/chunks.json`.
4. Al consultar, la pregunta también se convierte en un vector. Pinecone
   devuelve los chunks de vectores más parecidos. BM25, en paralelo, busca las
   palabras de la pregunta en `chunks.json`. El híbrido mezcla las dos listas
   y se queda con 5 chunks.

## Corpus

En `data/` está la documentación de la librería de pipelines: funciones de
Jenkins, AWS, Docker, Kubernetes, Helm, Jira y el resto. El `doc_id` de cada
chunk es el nombre del archivo, sin extensión.

El golden set apunta a estos documentos:

| Archivo | `doc_id` |
| --- | --- |
| `pipelineWarmUp.md` | `pipelineWarmUp` |
| `cleanUpFunctions.md` | `cleanUpFunctions` |
| `pythonLibFunctions.md` | `pythonLibFunctions` |
| `pamCredentials.md` | `pamCredentials` |
| `trivyFunctions.md` | `trivyFunctions` |
| `helmFunctions.md` | `helmFunctions` |
| `syftFunctions.md` | `syftFunctions` |
| `jiraFunctions.md` | `jiraFunctions` |
| `k8sFunctions.md` | `k8sFunctions` |
| `notificationsFunctions.md` | `notificationsFunctions` |
| `liquibaseFunctions.md` | `liquibaseFunctions` |
| `mobileFastlaneFunctions.md` | `mobileFastlaneFunctions` |

Cada chunk guarda `doc_id`, `source`, `page`, `category` y `tags`. `category`
y `tags` quedan iguales al `doc_id`.

Toda la documentación indexada vive en el namespace `pre-entrega4`. Otro tipo
de dato iría a otro namespace para no mezclar el ranking.

## Embeddings

El índice `rag-escalable-4` es serverless (`aws` / `us-east-1`), métrica coseno.
La dimensión la define el encoder activo.

El encoder por defecto es Ollama con `all-minilm` (384 dimensiones), el mismo
modelo local `all-MiniLM-L6-v2` que usa el RAG de Chroma. Hace falta Ollama
en `http://127.0.0.1:11434` y el modelo descargado:

```powershell
ollama pull all-minilm
```

## Cómo replicar el índice

Python 3.12, desde esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Completá `.env` (no se sube al repo):

```env
PINECONE_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
INDEX_NAME=rag-escalable-4
PINECONE_NAMESPACE=pre-entrega4
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBED_MODEL=all-minilm
```

Crear el índice si no existe, ingestar y evaluar:

```powershell
python setup_index.py
python ingest.py
python evaluate.py
```

`ingest.py` vuelve a llamar a `setup_index.py`, vacía solo el namespace
`pre-entrega4` y sube los chunks de nuevo. Los otros namespaces del proyecto
de Pinecone no se tocan.

Consulta libre (top 5):

```powershell
python rag.py "¿Qué método abstrae el comando install de un chart de Helm?"
```

En Windows, si la consola rompe los acentos: `python -X utf8 evaluate.py`.

## Recuperador híbrido

`RAGSystem` arma un `EnsembleRetriever` con pesos iguales:

1. `BM25Retriever` sobre los mismos chunks que se subieron (espejo local en `artifacts/chunks.json`, generado por la ingesta).
2. `PineconeVectorStore` en el namespace `pre-entrega4`.

## Evaluación

`eval/golden_set.json` tiene 12 preguntas sobre la librería de pipelines.
Cada una declara el `doc_id` del archivo que contiene la respuesta.
Un chunk es útil si su `doc_id` coincide con ese documento.

- **Recall@5:** 1 si el documento correcto aparece al menos una vez entre los 5.
- **Precision@5:** fracción de esos 5 cuyo `doc_id` es el esperado.

BM25 parte identificadores como `k8sFunctions.getVersionDeploy` para que el nombre del
método no se pierda como una sola palabra. La precisión queda por debajo de 1
porque el top 5 mezcla chunks de archivos vecinos: con un solo documento
correcto, el techo habitual es cerca de 0.40.

## Archivos

- `setup_index.py` — crea el índice serverless y lo recrea si cambia la dimensión
- `chunks.py` — corta los markdown en chunks de 600 tokens, con overlap de 80
- `ingest.py` — embeddings y upsert con metadata
- `rag.py` — clase `RAGSystem` (BM25 + Pinecone)
- `evaluate.py` — Precision@5 y Recall@5
- `embeddings.py` — Ollama `all-minilm`, o Gemini / OpenAI en 1536 dims
- `data/` — markdown de la librería
- `eval/golden_set.json` — benchmark

`.env`, `.venv` y `artifacts/` están en `.gitignore`.