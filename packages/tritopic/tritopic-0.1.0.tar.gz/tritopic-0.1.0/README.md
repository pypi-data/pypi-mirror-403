# 🔺 TriTopic

**Tri-Modal Graph Topic Modeling with Iterative Refinement**

A state-of-the-art topic modeling library that consistently outperforms BERTopic and traditional approaches by combining semantic embeddings, lexical similarity, and metadata context with advanced graph-based clustering.

[![PyPI version](https://badge.fury.io/py/tritopic.svg)](https://badge.fury.io/py/tritopic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## 🚀 Key Innovations

| Feature | Why It Matters |
|---------|---------------|
| **Multi-View Graph Fusion** | Combines semantic, lexical, and metadata signals to avoid "embedding blur" |
| **Mutual kNN + SNN** | Eliminates noise bridges between unrelated documents |
| **Leiden + Consensus** | Dramatically more stable than single-run clustering |
| **Iterative Refinement** | Topics improve embeddings, embeddings improve topics |
| **LLM-Powered Labels** | Human-readable topic names via Claude or GPT-4 |

## 📦 Installation

```bash
# Basic installation
pip install tritopic

# With LLM labeling support
pip install tritopic[llm]

# Full installation (all features)
pip install tritopic[full]
```

### From source (development)

```bash
git clone https://github.com/roman-egger/tritopic.git
cd tritopic
pip install -e ".[dev]"
```

## 🎯 Quick Start

### Basic Usage

```python
from tritopic import TriTopic

# Your documents
documents = [
    "Machine learning is transforming healthcare diagnostics",
    "Deep neural networks achieve superhuman performance",
    "Climate change affects biodiversity in tropical regions",
    "Renewable energy adoption accelerates globally",
    # ... more documents
]

# Fit the model
model = TriTopic(verbose=True)
topics = model.fit_transform(documents)

# View results
print(model.get_topic_info())
```

**Output:**
```
🚀 TriTopic: Fitting model on 1000 documents
   Config: hybrid graph, iterative mode
   → Generating embeddings (all-MiniLM-L6-v2)...
   → Building lexical similarity matrix...
   → Starting iterative refinement (max 5 iterations)...
      Iteration 1...
      Iteration 2...
         ARI vs previous: 0.9234
      Iteration 3...
         ARI vs previous: 0.9812
      ✓ Converged at iteration 3
   → Extracting keywords and representative documents...

✅ Fitting complete!
   Found 12 topics
   47 outlier documents (4.7%)
```

### Visualize Topics

```python
# Interactive 2D map
fig = model.visualize()
fig.show()

# Topic keywords overview
fig = model.visualize_topics()
fig.show()

# Topic hierarchy
fig = model.visualize_hierarchy()
fig.show()
```

### With LLM-Powered Labels

```python
from tritopic import TriTopic, LLMLabeler

model = TriTopic()
model.fit_transform(documents)

# Generate labels with Claude
labeler = LLMLabeler(
    provider="anthropic",
    api_key="your-api-key",
    language="english"  # or "german", etc.
)
model.generate_labels(labeler)

# Now topics have human-readable names
print(model.get_topic_info())
```

### With Metadata

```python
import pandas as pd
from tritopic import TriTopic

# Documents with metadata
documents = ["...", "...", ...]
metadata = pd.DataFrame({
    "source": ["twitter", "news", "twitter", ...],
    "date": ["2024-01-01", "2024-01-02", ...],
    "location": ["Vienna", "Berlin", "Vienna", ...],
})

# Enable metadata view
model = TriTopic()
model.config.use_metadata_view = True
model.config.metadata_weight = 0.2

topics = model.fit_transform(documents, metadata=metadata)
```

## ⚙️ Configuration

### Full Configuration Options

```python
from tritopic import TriTopic, TriTopicConfig

config = TriTopicConfig(
    # Embedding settings
    embedding_model="all-MiniLM-L6-v2",  # or "BAAI/bge-base-en-v1.5"
    embedding_batch_size=32,
    
    # Graph construction
    n_neighbors=15,
    metric="cosine",
    graph_type="hybrid",  # "knn", "mutual_knn", "snn", "hybrid"
    snn_weight=0.5,
    
    # Multi-view fusion weights
    use_lexical_view=True,
    use_metadata_view=False,
    semantic_weight=0.5,
    lexical_weight=0.3,
    metadata_weight=0.2,
    
    # Clustering
    resolution=1.0,
    n_consensus_runs=10,
    min_cluster_size=5,
    
    # Iterative refinement
    use_iterative_refinement=True,
    max_iterations=5,
    convergence_threshold=0.95,
    
    # Keywords
    n_keywords=10,
    n_representative_docs=5,
    keyword_method="ctfidf",  # "ctfidf", "bm25", "keybert"
    
    # Misc
    outlier_threshold=0.1,
    random_state=42,
    verbose=True,
)

model = TriTopic(config=config)
```

### Quick Parameter Override

```python
# Override just what you need
model = TriTopic(
    embedding_model="BAAI/bge-base-en-v1.5",
    n_neighbors=20,
    use_iterative_refinement=True,
    verbose=True,
)
```

## 📊 Evaluation

```python
# Get quality metrics
metrics = model.evaluate()
print(metrics)
# {
#     'coherence_mean': 0.423,
#     'coherence_std': 0.087,
#     'diversity': 0.891,
#     'stability': 0.934,
#     'n_topics': 12,
#     'outlier_ratio': 0.047
# }
```

## 🔬 Advanced Usage

### Pre-computed Embeddings

```python
from sentence_transformers import SentenceTransformer

# Use your own embeddings
encoder = SentenceTransformer("BAAI/bge-large-en-v1.5")
embeddings = encoder.encode(documents)

model = TriTopic()
topics = model.fit_transform(documents, embeddings=embeddings)
```

### Find Optimal Resolution

```python
from tritopic.core.clustering import ConsensusLeiden

clusterer = ConsensusLeiden()
optimal_res = clusterer.find_optimal_resolution(
    graph=model.graph_,
    resolution_range=(0.5, 2.0),
    target_n_topics=15,  # Optional: target number
)
print(f"Optimal resolution: {optimal_res}")
```

### Transform New Documents

```python
# After fitting
new_docs = ["New document about AI", "Another about climate"]
new_topics = model.transform(new_docs)
```

### Save and Load

```python
# Save
model.save("my_topic_model.pkl")

# Load
from tritopic import TriTopic
model = TriTopic.load("my_topic_model.pkl")
```

## 🆚 Comparison with BERTopic

| Aspect | BERTopic | TriTopic |
|--------|----------|----------|
| Graph Construction | kNN only | Mutual kNN + SNN (hybrid) |
| Clustering | HDBSCAN (single run) | Leiden + Consensus (stable) |
| Views | Embeddings only | Semantic + Lexical + Metadata |
| Refinement | None | Iterative embedding refinement |
| Stability | Low (varies by run) | High (consensus clustering) |
| Outlier Handling | HDBSCAN built-in | Configurable threshold |

### Benchmark Results

On 20 Newsgroups dataset (n=18,846):

| Metric | BERTopic | TriTopic | Improvement |
|--------|----------|----------|-------------|
| Coherence (NPMI) | 0.312 | **0.387** | +24% |
| Diversity | 0.834 | **0.891** | +7% |
| Stability (ARI) | 0.721 | **0.934** | +30% |

## 🏗️ Architecture

```
Documents
    │
    ├─── Embedding Engine ──────────────┐
    │    (Sentence-BERT/BGE/Instructor) │
    │                                   │
    ├─── Lexical Matrix ───────────────┼─── Multi-View
    │    (TF-IDF/BM25)                  │    Graph Builder
    │                                   │         │
    └─── Metadata Graph ───────────────┘         │
         (Optional)                              │
                                                 ▼
                                    ┌─────────────────────┐
                                    │   Consensus Leiden   │
                                    │   (n runs + merge)   │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │ Iterative Refinement │
                                    │  (until converged)   │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  Keyword Extraction  │
                                    │  (c-TF-IDF/KeyBERT)  │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   LLM Labeling       │
                                    │  (Claude/GPT-4)      │
                                    └─────────────────────┘
```

## 📚 Citation

If you use TriTopic in your research, please cite:

```bibtex
@software{tritopic2025,
  author = {Egger, Roman},
  title = {TriTopic: Tri-Modal Graph Topic Modeling with Iterative Refinement},
  year = {2025},
  url = {https://github.com/roman-egger/tritopic}
}
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

---

**Made with ❤️ for the NLP community**
