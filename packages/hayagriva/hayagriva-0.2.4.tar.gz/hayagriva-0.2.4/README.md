# Hayagriva – Modular Retrieval-Augmented Generation Framework

![Hayagriva](hayagriva.png)

सर्वविद्याप्रसूत्यर्थं हयग्रीवोऽवतारतः
वेदान् संरक्ष्य जगतां हितकारी सदा भवेत्

"To restore and protect all knowledge, Hayagriva has manifested. He safeguards the Vedas for the good of the world."

Hayagriva is a lightweight, modular Retrieval-Augmented Generation (RAG) framework that connects LLMs with efficient document retrieval. It focuses on grounded answers, fast iteration, and easy integration for developers and research teams.

---

## Key Features

### Retrieval-Augmented Generation
Combine contextual retrieval with LLMs to produce grounded, source-aware answers.

Supported LLM backends today: **Groq** and **OpenAI**.

### Retrieval Strategies
Hayagriva supports multiple retrieval strategies (depending on vector store):

* **Vector Search**: Dense semantic retrieval.
* **BM25**: Sparse keyword retrieval (Weaviate).
* **Hybrid Search**: Vector + keyword with configurable weighting (Weaviate).

### Chunking Strategies

* **Word (Default)**: Sliding window on word count.
* **Recursive**: Split by separators to preserve structure.
* **Semantic**: Embedding-aware topic shifts.
* **Hierarchical**: Parent/child chunking for broad + precise context.

### Modular Vector Stores

* **FAISS**: Lightweight, in-memory vector store.
* **Weaviate**: Production-grade vector DB with hybrid/BM25.
* **Pinecone**: Managed vector DB (vector-only search in current implementation).

### Flexible Document Handling

* Programmatic document ingestion.
* CLI ingestion of files and directories.
  * **Directory ingestion reads `.txt` files by default**.

Automatic chunking and metadata assignment are built in.

---

## Installation

### Default (Lightweight)
Core libraries only:
```bash
pip install hayagriva
```

### CPU Support (Recommended for Local Testing)
Installs `sentence-transformers` and `faiss-cpu`:
```bash
pip install "hayagriva[cpu]"
```

### GPU Support
Installs `sentence-transformers` and `faiss-gpu`:
```bash
pip install "hayagriva[cuda]"
```

---

## Python Usage

### Basic Example (FAISS + Vector Search)

```python
from hayagriva import Hayagriva, HayagrivaConfig

config = HayagrivaConfig(
    backend="groq",
    api_key="YOUR_GROQ_KEY",
    model="llama-3.1-8b-instant",
)

rag = Hayagriva(config)
rag.add_documents(["Hayagriva restores forgotten knowledge."])

response = "".join(rag.ask("Who retrieved the lost Vedas?"))
print(response)
```

### Structured Response (Answer + Metadata)

```python
resp = rag.ask("Who retrieved the lost Vedas?", return_metadata=True)
print(resp["answer"])
print(resp["chunks"][0])
print(resp["retrieval"]["strategy"])
```

Returned metadata includes: retrieved chunk ranks/scores, chunking strategy, retrieval strategy, model backend, and vector store.

### Customizing Embeddings

```python
config = HayagrivaConfig(
    backend="groq",
    api_key="YOUR_KEY",
    embedding_model="intfloat/multilingual-e5-large",
)
```

### Advanced Example (Weaviate + Hybrid Search)

```python
from hayagriva import Hayagriva, HayagrivaConfig
from hayagriva.config import WeaviateConfig, RetrievalConfig, ChunkingConfig

weaviate_config = WeaviateConfig(
    url="http://localhost:8080",
    index_name="HayagrivaDocs",
)

config = HayagrivaConfig(
    backend="groq",
    api_key="YOUR_GROQ_KEY",
    vector_store="weaviate",
    weaviate=weaviate_config,
    retrieval=RetrievalConfig(strategy="hybrid", alpha=0.5, top_k=4),
    chunking=ChunkingConfig(strategy="recursive", chunk_size=500, overlap=50),
)

rag = Hayagriva(config)
rag.add_documents(["Hayagriva is an avatar of Vishnu."])

for token in rag.ask("Who is Hayagriva?"):
    print(token, end="", flush=True)
```

---

## CLI Usage

### Ingest Files

```bash
hayagriva ingest ./docs
```

### Query

```bash
hayagriva query "What is RAG?"
```

---

## Requirements

* Python 3.10+
* API key for Groq or OpenAI

Optional (only if you use local embeddings or FAISS):

* sentence-transformers
* faiss-cpu or faiss-gpu

If using external vector databases:

* weaviate-client
* pinecone-client

---

## Roadmap

### Expanded LLM Provider Support

* Anthropic Claude
* Google Gemini
* DeepSeek
* Local GGUF models and llama.cpp

### Additional Vector Database Integration

* ChromaDB
* Additional pluggable backends

### Memory-Augmented Chat

* Multi-turn memory
* Embedding-based long-term memory
* Summarization-based memory compression

---

## Use Cases

* Retrieval-augmented assistants
* Knowledge-base and enterprise search
* Research and benchmarking of RAG pipelines
* Lightweight production deployments
* Internal document Q&A systems

---

## Contributing

Contributions to model integrations, retrieval modules, and documentation are welcome. Submit issues or pull requests.

---

## Support

For questions, bugs, or feature requests, open an issue on the project repository.
