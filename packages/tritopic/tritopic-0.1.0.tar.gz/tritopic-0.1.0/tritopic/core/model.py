"""
TriTopic: Main Model Class
===========================

The core class that orchestrates all components of the topic modeling pipeline.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd
from tqdm import tqdm

from tritopic.core.embeddings import EmbeddingEngine
from tritopic.core.graph_builder import GraphBuilder
from tritopic.core.clustering import ConsensusLeiden
from tritopic.core.keywords import KeywordExtractor
from tritopic.utils.metrics import compute_coherence, compute_diversity, compute_stability


@dataclass
class TopicInfo:
    """Container for topic information."""
    
    topic_id: int
    size: int
    keywords: list[str]
    keyword_scores: list[float]
    representative_docs: list[int]
    label: str | None = None
    description: str | None = None
    centroid: np.ndarray | None = None
    coherence: float | None = None


@dataclass
class TriTopicConfig:
    """Configuration for TriTopic model."""
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    
    # Graph settings
    n_neighbors: int = 15
    metric: str = "cosine"
    graph_type: Literal["mutual_knn", "snn", "hybrid"] = "hybrid"
    snn_weight: float = 0.5
    
    # Multi-view settings
    use_lexical_view: bool = True
    use_metadata_view: bool = False
    lexical_weight: float = 0.3
    metadata_weight: float = 0.2
    semantic_weight: float = 0.5
    
    # Clustering settings
    resolution: float = 1.0
    resolution_range: tuple[float, float] | None = None
    n_consensus_runs: int = 10
    min_cluster_size: int = 5
    
    # Iterative refinement
    use_iterative_refinement: bool = True
    max_iterations: int = 5
    convergence_threshold: float = 0.95
    
    # Keyword extraction
    n_keywords: int = 10
    n_representative_docs: int = 5
    keyword_method: Literal["ctfidf", "bm25", "keybert"] = "ctfidf"
    
    # Outlier handling
    outlier_threshold: float = 0.1
    
    # Misc
    random_state: int = 42
    verbose: bool = True


class TriTopic:
    """
    Tri-Modal Graph Topic Modeling with Iterative Refinement.
    
    A state-of-the-art topic modeling approach that combines semantic embeddings,
    lexical similarity, and optional metadata to create robust, interpretable topics.
    
    Key innovations:
    - Multi-view graph fusion (semantic + lexical + metadata)
    - Leiden clustering with consensus for stability
    - Iterative refinement loop for optimal topic separation
    - Advanced keyword extraction with representative documents
    - Optional LLM-powered topic labeling
    
    Parameters
    ----------
    config : TriTopicConfig, optional
        Configuration object. If None, uses defaults.
    embedding_model : str, optional
        Name of sentence-transformers model. Default: "all-MiniLM-L6-v2"
    n_neighbors : int, optional
        Number of neighbors for graph construction. Default: 15
    n_topics : int or "auto", optional
        Number of topics. "auto" uses Leiden's natural resolution. Default: "auto"
    use_iterative_refinement : bool, optional
        Whether to use the iterative refinement loop. Default: True
    verbose : bool, optional
        Print progress information. Default: True
    
    Attributes
    ----------
    topics_ : list[TopicInfo]
        Information about each discovered topic.
    labels_ : np.ndarray
        Topic assignment for each document.
    embeddings_ : np.ndarray
        Document embeddings.
    graph_ : igraph.Graph
        The constructed similarity graph.
    topic_embeddings_ : np.ndarray
        Centroid embeddings for each topic.
    
    Examples
    --------
    Basic usage:
    
    >>> from tritopic import TriTopic
    >>> model = TriTopic(n_neighbors=15, verbose=True)
    >>> topics = model.fit_transform(documents)
    >>> print(model.get_topic_info())
    
    With metadata:
    
    >>> model = TriTopic()
    >>> model.config.use_metadata_view = True
    >>> topics = model.fit_transform(documents, metadata=df[['source', 'date']])
    
    With LLM labeling:
    
    >>> from tritopic import TriTopic, LLMLabeler
    >>> model = TriTopic()
    >>> model.fit_transform(documents)
    >>> labeler = LLMLabeler(provider="anthropic", api_key="...")
    >>> model.generate_labels(labeler)
    """
    
    def __init__(
        self,
        config: TriTopicConfig | None = None,
        embedding_model: str | None = None,
        n_neighbors: int | None = None,
        n_topics: int | Literal["auto"] = "auto",
        use_iterative_refinement: bool | None = None,
        verbose: bool | None = None,
        random_state: int | None = None,
    ):
        # Initialize config
        self.config = config or TriTopicConfig()
        
        # Override config with explicit parameters
        if embedding_model is not None:
            self.config.embedding_model = embedding_model
        if n_neighbors is not None:
            self.config.n_neighbors = n_neighbors
        if use_iterative_refinement is not None:
            self.config.use_iterative_refinement = use_iterative_refinement
        if verbose is not None:
            self.config.verbose = verbose
        if random_state is not None:
            self.config.random_state = random_state
            
        self.n_topics = n_topics
        
        # Initialize components
        self._embedding_engine = EmbeddingEngine(
            model_name=self.config.embedding_model,
            batch_size=self.config.embedding_batch_size,
        )
        self._graph_builder = GraphBuilder(
            n_neighbors=self.config.n_neighbors,
            metric=self.config.metric,
            graph_type=self.config.graph_type,
            snn_weight=self.config.snn_weight,
        )
        self._clusterer = ConsensusLeiden(
            resolution=self.config.resolution,
            n_runs=self.config.n_consensus_runs,
            random_state=self.config.random_state,
        )
        self._keyword_extractor = KeywordExtractor(
            method=self.config.keyword_method,
            n_keywords=self.config.n_keywords,
        )
        
        # State
        self.topics_: list[TopicInfo] = []
        self.labels_: np.ndarray | None = None
        self.embeddings_: np.ndarray | None = None
        self.lexical_matrix_: Any | None = None
        self.graph_: Any | None = None
        self.topic_embeddings_: np.ndarray | None = None
        self.documents_: list[str] | None = None
        self._is_fitted: bool = False
        self._iteration_history: list[dict] = []
        
    def fit(
        self,
        documents: list[str],
        embeddings: np.ndarray | None = None,
        metadata: pd.DataFrame | None = None,
    ) -> "TriTopic":
        """
        Fit the topic model to documents.
        
        Parameters
        ----------
        documents : list[str]
            List of document texts.
        embeddings : np.ndarray, optional
            Pre-computed embeddings. If None, computed automatically.
        metadata : pd.DataFrame, optional
            Document metadata for the metadata view.
            
        Returns
        -------
        self : TriTopic
            Fitted model.
        """
        self.documents_ = documents
        n_docs = len(documents)
        
        if self.config.verbose:
            print(f"🚀 TriTopic: Fitting model on {n_docs} documents")
            print(f"   Config: {self.config.graph_type} graph, "
                  f"{'iterative' if self.config.use_iterative_refinement else 'single-pass'} mode")
        
        # Step 1: Generate embeddings
        if embeddings is not None:
            self.embeddings_ = embeddings
            if self.config.verbose:
                print("   ✓ Using provided embeddings")
        else:
            if self.config.verbose:
                print(f"   → Generating embeddings ({self.config.embedding_model})...")
            self.embeddings_ = self._embedding_engine.encode(documents)
        
        # Step 2: Build lexical representation
        if self.config.use_lexical_view:
            if self.config.verbose:
                print("   → Building lexical similarity matrix...")
            self.lexical_matrix_ = self._graph_builder.build_lexical_matrix(documents)
        
        # Step 3: Build metadata graph (if provided)
        metadata_graph = None
        if self.config.use_metadata_view and metadata is not None:
            if self.config.verbose:
                print("   → Building metadata similarity graph...")
            metadata_graph = self._graph_builder.build_metadata_graph(metadata)
        
        # Step 4: Main fitting loop
        if self.config.use_iterative_refinement:
            self._fit_iterative(documents, metadata_graph)
        else:
            self._fit_single_pass(documents, metadata_graph)
        
        # Step 5: Extract keywords and representative docs
        if self.config.verbose:
            print("   → Extracting keywords and representative documents...")
        self._extract_topic_info(documents)
        
        # Step 6: Compute topic centroids
        self._compute_topic_centroids()
        
        self._is_fitted = True
        
        if self.config.verbose:
            n_topics = len([t for t in self.topics_ if t.topic_id != -1])
            n_outliers = np.sum(self.labels_ == -1) if self.labels_ is not None else 0
            print(f"\n✅ Fitting complete!")
            print(f"   Found {n_topics} topics")
            print(f"   {n_outliers} outlier documents ({100*n_outliers/n_docs:.1f}%)")
        
        return self
    
    def _fit_single_pass(
        self,
        documents: list[str],
        metadata_graph: Any | None = None,
    ) -> None:
        """Single-pass fitting without iterative refinement."""
        # Build graph
        if self.config.verbose:
            print("   → Building multi-view graph...")
            
        self.graph_ = self._graph_builder.build_multiview_graph(
            semantic_embeddings=self.embeddings_,
            lexical_matrix=self.lexical_matrix_ if self.config.use_lexical_view else None,
            metadata_graph=metadata_graph,
            weights={
                "semantic": self.config.semantic_weight,
                "lexical": self.config.lexical_weight,
                "metadata": self.config.metadata_weight,
            }
        )
        
        # Cluster
        if self.config.verbose:
            print(f"   → Running Leiden consensus clustering ({self.config.n_consensus_runs} runs)...")
            
        self.labels_ = self._clusterer.fit_predict(
            self.graph_,
            min_cluster_size=self.config.min_cluster_size,
        )
    
    def _fit_iterative(
        self,
        documents: list[str],
        metadata_graph: Any | None = None,
    ) -> None:
        """Iterative refinement fitting loop."""
        if self.config.verbose:
            print(f"   → Starting iterative refinement (max {self.config.max_iterations} iterations)...")
        
        current_embeddings = self.embeddings_.copy()
        previous_labels = None
        
        for iteration in range(self.config.max_iterations):
            if self.config.verbose:
                print(f"      Iteration {iteration + 1}...")
            
            # Build graph with current embeddings
            self.graph_ = self._graph_builder.build_multiview_graph(
                semantic_embeddings=current_embeddings,
                lexical_matrix=self.lexical_matrix_ if self.config.use_lexical_view else None,
                metadata_graph=metadata_graph,
                weights={
                    "semantic": self.config.semantic_weight,
                    "lexical": self.config.lexical_weight,
                    "metadata": self.config.metadata_weight,
                }
            )
            
            # Cluster
            self.labels_ = self._clusterer.fit_predict(
                self.graph_,
                min_cluster_size=self.config.min_cluster_size,
            )
            
            # Check convergence
            if previous_labels is not None:
                from sklearn.metrics import adjusted_rand_score
                ari = adjusted_rand_score(previous_labels, self.labels_)
                self._iteration_history.append({
                    "iteration": iteration + 1,
                    "ari": ari,
                    "n_topics": len(np.unique(self.labels_[self.labels_ != -1])),
                })
                
                if self.config.verbose:
                    print(f"         ARI vs previous: {ari:.4f}")
                
                if ari >= self.config.convergence_threshold:
                    if self.config.verbose:
                        print(f"      ✓ Converged at iteration {iteration + 1}")
                    break
            
            previous_labels = self.labels_.copy()
            
            # Refine embeddings based on topic structure
            current_embeddings = self._refine_embeddings(
                documents, self.embeddings_, self.labels_
            )
        
        # Store final refined embeddings
        self.embeddings_ = current_embeddings
    
    def _refine_embeddings(
        self,
        documents: list[str],
        original_embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> np.ndarray:
        """
        Refine embeddings by incorporating topic context.
        
        This is the key innovation: we modify embeddings to be more
        topic-aware by pulling documents toward their topic centroid.
        """
        refined = original_embeddings.copy()
        unique_labels = np.unique(labels[labels != -1])
        
        # Compute topic centroids
        centroids = {}
        for label in unique_labels:
            mask = labels == label
            centroids[label] = original_embeddings[mask].mean(axis=0)
        
        # Soft refinement: blend original embedding with topic centroid
        blend_factor = 0.2  # How much to pull toward centroid
        
        for i, label in enumerate(labels):
            if label != -1:  # Skip outliers
                centroid = centroids[label]
                refined[i] = (1 - blend_factor) * refined[i] + blend_factor * centroid
                # Re-normalize
                refined[i] = refined[i] / np.linalg.norm(refined[i])
        
        return refined
    
    def _extract_topic_info(self, documents: list[str]) -> None:
        """Extract keywords and representative documents for each topic."""
        self.topics_ = []
        unique_labels = np.unique(self.labels_)
        
        for label in unique_labels:
            mask = self.labels_ == label
            topic_docs = [documents[i] for i in np.where(mask)[0]]
            topic_indices = np.where(mask)[0]
            
            # Extract keywords
            keywords, scores = self._keyword_extractor.extract(
                topic_docs, 
                all_docs=documents,
                n_keywords=self.config.n_keywords,
            )
            
            # Find representative documents (closest to centroid)
            if self.embeddings_ is not None and label != -1:
                topic_embeddings = self.embeddings_[mask]
                centroid = topic_embeddings.mean(axis=0)
                distances = np.linalg.norm(topic_embeddings - centroid, axis=1)
                top_indices = np.argsort(distances)[:self.config.n_representative_docs]
                representative_docs = [int(topic_indices[i]) for i in top_indices]
            else:
                representative_docs = list(topic_indices[:self.config.n_representative_docs])
            
            topic_info = TopicInfo(
                topic_id=int(label),
                size=int(mask.sum()),
                keywords=keywords,
                keyword_scores=scores,
                representative_docs=representative_docs,
                label=None,
                description=None,
            )
            self.topics_.append(topic_info)
        
        # Sort by size (excluding outliers)
        self.topics_ = sorted(
            self.topics_,
            key=lambda t: (t.topic_id == -1, -t.size)
        )
    
    def _compute_topic_centroids(self) -> None:
        """Compute centroid embeddings for each topic."""
        if self.embeddings_ is None:
            return
            
        unique_labels = [t.topic_id for t in self.topics_ if t.topic_id != -1]
        self.topic_embeddings_ = np.zeros((len(unique_labels), self.embeddings_.shape[1]))
        
        for i, label in enumerate(unique_labels):
            mask = self.labels_ == label
            self.topic_embeddings_[i] = self.embeddings_[mask].mean(axis=0)
            
            # Store in topic info
            for topic in self.topics_:
                if topic.topic_id == label:
                    topic.centroid = self.topic_embeddings_[i]
                    break
    
    def fit_transform(
        self,
        documents: list[str],
        embeddings: np.ndarray | None = None,
        metadata: pd.DataFrame | None = None,
    ) -> np.ndarray:
        """
        Fit the model and return topic assignments.
        
        Parameters
        ----------
        documents : list[str]
            List of document texts.
        embeddings : np.ndarray, optional
            Pre-computed embeddings.
        metadata : pd.DataFrame, optional
            Document metadata.
            
        Returns
        -------
        labels : np.ndarray
            Topic assignment for each document. -1 indicates outlier.
        """
        self.fit(documents, embeddings, metadata)
        return self.labels_
    
    def transform(self, documents: list[str]) -> np.ndarray:
        """
        Assign topics to new documents.
        
        Parameters
        ----------
        documents : list[str]
            New documents to classify.
            
        Returns
        -------
        labels : np.ndarray
            Topic assignments.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Encode new documents
        new_embeddings = self._embedding_engine.encode(documents)
        
        # Find nearest topic centroid
        labels = np.zeros(len(documents), dtype=int)
        
        for i, emb in enumerate(new_embeddings):
            distances = np.linalg.norm(self.topic_embeddings_ - emb, axis=1)
            nearest_topic_idx = np.argmin(distances)
            
            # Check if it's an outlier (too far from any centroid)
            if distances[nearest_topic_idx] > self.config.outlier_threshold * 2:
                labels[i] = -1
            else:
                # Map index back to topic_id
                non_outlier_topics = [t for t in self.topics_ if t.topic_id != -1]
                labels[i] = non_outlier_topics[nearest_topic_idx].topic_id
        
        return labels
    
    def get_topic_info(self) -> pd.DataFrame:
        """
        Get a DataFrame with topic information.
        
        Returns
        -------
        df : pd.DataFrame
            DataFrame with columns: Topic, Size, Keywords, Label, Coherence
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        data = []
        for topic in self.topics_:
            data.append({
                "Topic": topic.topic_id,
                "Size": topic.size,
                "Keywords": ", ".join(topic.keywords[:5]),
                "All_Keywords": topic.keywords,
                "Keyword_Scores": topic.keyword_scores,
                "Label": topic.label or f"Topic {topic.topic_id}",
                "Description": topic.description,
                "Representative_Docs": topic.representative_docs,
                "Coherence": topic.coherence,
            })
        
        return pd.DataFrame(data)
    
    def get_topic(self, topic_id: int) -> TopicInfo | None:
        """Get information about a specific topic."""
        for topic in self.topics_:
            if topic.topic_id == topic_id:
                return topic
        return None
    
    def get_representative_docs(
        self,
        topic_id: int,
        n_docs: int = 5,
    ) -> list[tuple[int, str]]:
        """
        Get representative documents for a topic.
        
        Parameters
        ----------
        topic_id : int
            Topic ID.
        n_docs : int
            Number of documents to return.
            
        Returns
        -------
        docs : list[tuple[int, str]]
            List of (index, document_text) tuples.
        """
        if not self._is_fitted or self.documents_ is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        topic = self.get_topic(topic_id)
        if topic is None:
            raise ValueError(f"Topic {topic_id} not found.")
        
        indices = topic.representative_docs[:n_docs]
        return [(idx, self.documents_[idx]) for idx in indices]
    
    def generate_labels(
        self,
        labeler: "LLMLabeler",
        topics: list[int] | None = None,
    ) -> None:
        """
        Generate labels for topics using an LLM.
        
        Parameters
        ----------
        labeler : LLMLabeler
            Configured LLM labeler instance.
        topics : list[int], optional
            Specific topics to label. If None, labels all.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        target_topics = topics or [t.topic_id for t in self.topics_ if t.topic_id != -1]
        
        for topic_id in tqdm(target_topics, desc="Generating labels", disable=not self.config.verbose):
            topic = self.get_topic(topic_id)
            if topic is None:
                continue
            
            # Get representative docs
            rep_docs = self.get_representative_docs(topic_id, n_docs=5)
            doc_texts = [doc for _, doc in rep_docs]
            
            # Generate label
            label, description = labeler.generate_label(
                keywords=topic.keywords,
                representative_docs=doc_texts,
            )
            
            topic.label = label
            topic.description = description
    
    def visualize(
        self,
        method: Literal["umap", "pacmap"] = "umap",
        color_by: Literal["topic", "custom"] = "topic",
        custom_labels: list[str] | None = None,
        show_outliers: bool = True,
        interactive: bool = True,
        **kwargs,
    ):
        """
        Visualize topics in 2D.
        
        Parameters
        ----------
        method : str
            Dimensionality reduction method. "umap" or "pacmap".
        color_by : str
            How to color points. "topic" uses topic assignments.
        custom_labels : list[str], optional
            Custom labels for hover text.
        show_outliers : bool
            Whether to show outlier documents.
        interactive : bool
            If True, returns interactive Plotly figure.
        **kwargs
            Additional arguments passed to the visualizer.
            
        Returns
        -------
        fig : plotly.graph_objects.Figure
            Interactive visualization.
        """
        from tritopic.visualization.plotter import TopicVisualizer
        
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        visualizer = TopicVisualizer(method=method)
        
        return visualizer.plot_documents(
            embeddings=self.embeddings_,
            labels=self.labels_,
            documents=self.documents_,
            topics=self.topics_,
            show_outliers=show_outliers,
            interactive=interactive,
            **kwargs,
        )
    
    def visualize_hierarchy(self, **kwargs):
        """Visualize topic hierarchy as a dendrogram."""
        from tritopic.visualization.plotter import TopicVisualizer
        
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        visualizer = TopicVisualizer()
        return visualizer.plot_hierarchy(
            topic_embeddings=self.topic_embeddings_,
            topics=self.topics_,
            **kwargs,
        )
    
    def visualize_topics(self, **kwargs):
        """Visualize topics as a heatmap or bar chart."""
        from tritopic.visualization.plotter import TopicVisualizer
        
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        visualizer = TopicVisualizer()
        return visualizer.plot_topics(
            topics=self.topics_,
            **kwargs,
        )
    
    def evaluate(self) -> dict[str, float]:
        """
        Evaluate topic model quality.
        
        Returns
        -------
        metrics : dict
            Dictionary with coherence, diversity, and stability scores.
        """
        if not self._is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Compute coherence for each topic
        coherences = []
        for topic in self.topics_:
            if topic.topic_id != -1:
                coh = compute_coherence(
                    topic.keywords,
                    [self.documents_[i] for i in np.where(self.labels_ == topic.topic_id)[0]]
                )
                topic.coherence = coh
                coherences.append(coh)
        
        # Compute diversity
        all_keywords = [kw for t in self.topics_ if t.topic_id != -1 for kw in t.keywords]
        diversity = compute_diversity(all_keywords, n_topics=len(coherences))
        
        # Get stability from consensus clustering
        stability = self._clusterer.stability_score_ if hasattr(self._clusterer, 'stability_score_') else None
        
        metrics = {
            "coherence_mean": float(np.mean(coherences)) if coherences else 0.0,
            "coherence_std": float(np.std(coherences)) if coherences else 0.0,
            "diversity": diversity,
            "stability": stability,
            "n_topics": len([t for t in self.topics_ if t.topic_id != -1]),
            "outlier_ratio": float(np.mean(self.labels_ == -1)) if self.labels_ is not None else 0.0,
        }
        
        if self.config.verbose:
            print("\n📊 Evaluation Metrics:")
            print(f"   Coherence (mean): {metrics['coherence_mean']:.4f}")
            print(f"   Diversity: {metrics['diversity']:.4f}")
            if stability:
                print(f"   Stability: {stability:.4f}")
            print(f"   Outlier ratio: {metrics['outlier_ratio']:.2%}")
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        import pickle
        
        state = {
            "config": self.config,
            "topics_": self.topics_,
            "labels_": self.labels_,
            "embeddings_": self.embeddings_,
            "topic_embeddings_": self.topic_embeddings_,
            "documents_": self.documents_,
            "_is_fitted": self._is_fitted,
            "_iteration_history": self._iteration_history,
        }
        
        with open(path, "wb") as f:
            pickle.dump(state, f)
        
        if self.config.verbose:
            print(f"💾 Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> "TriTopic":
        """Load model from disk."""
        import pickle
        
        with open(path, "rb") as f:
            state = pickle.load(f)
        
        model = cls(config=state["config"])
        model.topics_ = state["topics_"]
        model.labels_ = state["labels_"]
        model.embeddings_ = state["embeddings_"]
        model.topic_embeddings_ = state["topic_embeddings_"]
        model.documents_ = state["documents_"]
        model._is_fitted = state["_is_fitted"]
        model._iteration_history = state["_iteration_history"]
        
        return model
    
    def __repr__(self) -> str:
        status = "fitted" if self._is_fitted else "not fitted"
        n_topics = len([t for t in self.topics_ if t.topic_id != -1]) if self._is_fitted else "?"
        return f"TriTopic(n_topics={n_topics}, status={status})"
