"""
Graph Builder for TriTopic
============================

Constructs similarity graphs using multiple strategies:
- Mutual kNN: Only keep edges where both nodes are in each other's neighborhood
- SNN (Shared Nearest Neighbors): Weight edges by number of shared neighbors
- Multi-view fusion: Combine semantic, lexical, and metadata graphs
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class GraphBuilder:
    """
    Build similarity graphs for topic modeling.
    
    Supports multiple graph construction strategies for robust clustering.
    
    Parameters
    ----------
    n_neighbors : int
        Number of neighbors for kNN graph. Default: 15
    metric : str
        Distance metric. Default: "cosine"
    graph_type : str
        Type of graph: "knn", "mutual_knn", "snn", or "hybrid"
    snn_weight : float
        Weight for SNN edges in hybrid mode. Default: 0.5
    """
    
    def __init__(
        self,
        n_neighbors: int = 15,
        metric: str = "cosine",
        graph_type: Literal["knn", "mutual_knn", "snn", "hybrid"] = "hybrid",
        snn_weight: float = 0.5,
    ):
        self.n_neighbors = n_neighbors
        self.metric = metric
        self.graph_type = graph_type
        self.snn_weight = snn_weight
        
        self._tfidf_vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
        )
    
    def build_knn_graph(
        self,
        embeddings: np.ndarray,
        n_neighbors: int | None = None,
    ) -> csr_matrix:
        """
        Build a basic kNN graph.
        
        Parameters
        ----------
        embeddings : np.ndarray
            Document embeddings of shape (n_docs, n_dims).
        n_neighbors : int, optional
            Override default n_neighbors.
            
        Returns
        -------
        adjacency : csr_matrix
            Sparse adjacency matrix with cosine similarity weights.
        """
        k = n_neighbors or self.n_neighbors
        n_samples = embeddings.shape[0]
        
        # Fit nearest neighbors
        nn = NearestNeighbors(
            n_neighbors=min(k + 1, n_samples),  # +1 because point is its own neighbor
            metric=self.metric,
            algorithm="auto",
        )
        nn.fit(embeddings)
        
        # Get distances and indices
        distances, indices = nn.kneighbors(embeddings)
        
        # Convert to similarity and build sparse matrix
        if self.metric == "cosine":
            # Cosine distance to similarity
            similarities = 1 - distances
        else:
            # For other metrics, use inverse distance
            similarities = 1 / (1 + distances)
        
        # Build adjacency matrix
        adjacency = lil_matrix((n_samples, n_samples))
        
        for i in range(n_samples):
            for j_idx, j in enumerate(indices[i]):
                if i != j:  # Skip self-loops
                    adjacency[i, j] = similarities[i, j_idx]
        
        return adjacency.tocsr()
    
    def build_mutual_knn_graph(
        self,
        embeddings: np.ndarray,
        n_neighbors: int | None = None,
    ) -> csr_matrix:
        """
        Build a mutual kNN graph.
        
        Edge (i, j) exists only if i is in j's neighbors AND j is in i's neighbors.
        This removes "one-way" connections that often represent noise.
        
        Parameters
        ----------
        embeddings : np.ndarray
            Document embeddings.
        n_neighbors : int, optional
            Override default n_neighbors.
            
        Returns
        -------
        adjacency : csr_matrix
            Sparse adjacency matrix.
        """
        k = n_neighbors or self.n_neighbors
        n_samples = embeddings.shape[0]
        
        # Get kNN graph first
        nn = NearestNeighbors(
            n_neighbors=min(k + 1, n_samples),
            metric=self.metric,
            algorithm="auto",
        )
        nn.fit(embeddings)
        distances, indices = nn.kneighbors(embeddings)
        
        if self.metric == "cosine":
            similarities = 1 - distances
        else:
            similarities = 1 / (1 + distances)
        
        # Build neighbor sets for mutual check
        neighbor_sets = [set(indices[i][1:]) for i in range(n_samples)]  # Skip self
        
        # Build mutual kNN adjacency
        adjacency = lil_matrix((n_samples, n_samples))
        
        for i in range(n_samples):
            for j_idx, j in enumerate(indices[i][1:], 1):  # Skip self
                # Check if mutual
                if i in neighbor_sets[j]:
                    # Average the similarities
                    sim_ij = similarities[i, j_idx]
                    # Find j's similarity to i
                    j_indices = list(indices[j])
                    if i in j_indices:
                        sim_ji = similarities[j, j_indices.index(i)]
                    else:
                        sim_ji = sim_ij
                    
                    avg_sim = (sim_ij + sim_ji) / 2
                    adjacency[i, j] = avg_sim
                    adjacency[j, i] = avg_sim
        
        return adjacency.tocsr()
    
    def build_snn_graph(
        self,
        embeddings: np.ndarray,
        n_neighbors: int | None = None,
    ) -> csr_matrix:
        """
        Build a Shared Nearest Neighbors (SNN) graph.
        
        Edge weight = number of shared neighbors between two nodes.
        This is very robust against noise and outliers.
        
        Parameters
        ----------
        embeddings : np.ndarray
            Document embeddings.
        n_neighbors : int, optional
            Override default n_neighbors.
            
        Returns
        -------
        adjacency : csr_matrix
            Sparse adjacency matrix with SNN weights.
        """
        k = n_neighbors or self.n_neighbors
        n_samples = embeddings.shape[0]
        
        # Get kNN
        nn = NearestNeighbors(
            n_neighbors=min(k + 1, n_samples),
            metric=self.metric,
            algorithm="auto",
        )
        nn.fit(embeddings)
        _, indices = nn.kneighbors(embeddings)
        
        # Build neighbor sets
        neighbor_sets = [set(indices[i]) for i in range(n_samples)]
        
        # Compute SNN: edge weight = |N(i) ∩ N(j)|
        adjacency = lil_matrix((n_samples, n_samples))
        
        for i in range(n_samples):
            for j in neighbor_sets[i]:
                if i < j:  # Avoid duplicate computation
                    shared = len(neighbor_sets[i] & neighbor_sets[j])
                    if shared > 0:
                        # Normalize by k
                        weight = shared / k
                        adjacency[i, j] = weight
                        adjacency[j, i] = weight
        
        return adjacency.tocsr()
    
    def build_hybrid_graph(
        self,
        embeddings: np.ndarray,
        n_neighbors: int | None = None,
    ) -> csr_matrix:
        """
        Build a hybrid graph combining mutual kNN and SNN.
        
        This gives the best of both worlds:
        - Mutual kNN for strong direct connections
        - SNN for structural similarity
        
        Parameters
        ----------
        embeddings : np.ndarray
            Document embeddings.
        n_neighbors : int, optional
            Override default n_neighbors.
            
        Returns
        -------
        adjacency : csr_matrix
            Combined adjacency matrix.
        """
        mutual_adj = self.build_mutual_knn_graph(embeddings, n_neighbors)
        snn_adj = self.build_snn_graph(embeddings, n_neighbors)
        
        # Normalize both
        mutual_max = mutual_adj.max() if mutual_adj.nnz > 0 else 1
        snn_max = snn_adj.max() if snn_adj.nnz > 0 else 1
        
        if mutual_max > 0:
            mutual_adj = mutual_adj / mutual_max
        if snn_max > 0:
            snn_adj = snn_adj / snn_max
        
        # Combine
        combined = (1 - self.snn_weight) * mutual_adj + self.snn_weight * snn_adj
        
        return combined.tocsr()
    
    def build_lexical_matrix(
        self,
        documents: list[str],
    ) -> csr_matrix:
        """
        Build TF-IDF matrix for lexical similarity.
        
        Parameters
        ----------
        documents : list[str]
            Document texts.
            
        Returns
        -------
        tfidf_matrix : csr_matrix
            TF-IDF sparse matrix.
        """
        tfidf_matrix = self._tfidf_vectorizer.fit_transform(documents)
        return tfidf_matrix
    
    def build_lexical_graph(
        self,
        tfidf_matrix: csr_matrix,
        n_neighbors: int | None = None,
    ) -> csr_matrix:
        """
        Build lexical similarity graph from TF-IDF.
        
        Parameters
        ----------
        tfidf_matrix : csr_matrix
            TF-IDF matrix.
        n_neighbors : int, optional
            Override default n_neighbors.
            
        Returns
        -------
        adjacency : csr_matrix
            Lexical similarity adjacency matrix.
        """
        k = n_neighbors or self.n_neighbors
        n_samples = tfidf_matrix.shape[0]
        
        # Use NearestNeighbors with cosine metric on TF-IDF
        nn = NearestNeighbors(
            n_neighbors=min(k + 1, n_samples),
            metric="cosine",
            algorithm="brute",  # For sparse matrices
        )
        nn.fit(tfidf_matrix)
        distances, indices = nn.kneighbors(tfidf_matrix)
        
        # Convert distance to similarity
        similarities = 1 - distances
        
        # Build mutual kNN for lexical
        neighbor_sets = [set(indices[i][1:]) for i in range(n_samples)]
        adjacency = lil_matrix((n_samples, n_samples))
        
        for i in range(n_samples):
            for j_idx, j in enumerate(indices[i][1:], 1):
                if i in neighbor_sets[j]:
                    adjacency[i, j] = similarities[i, j_idx]
                    adjacency[j, i] = similarities[i, j_idx]
        
        return adjacency.tocsr()
    
    def build_metadata_graph(
        self,
        metadata: "pd.DataFrame",
    ) -> csr_matrix:
        """
        Build metadata similarity graph.
        
        Documents with matching metadata get connected.
        
        Parameters
        ----------
        metadata : pd.DataFrame
            Metadata DataFrame with same index as documents.
            
        Returns
        -------
        adjacency : csr_matrix
            Metadata similarity adjacency matrix.
        """
        import pandas as pd
        
        n_samples = len(metadata)
        adjacency = lil_matrix((n_samples, n_samples))
        
        # For each categorical column, connect matching documents
        for col in metadata.columns:
            if metadata[col].dtype == "object" or metadata[col].dtype.name == "category":
                # Categorical: exact match
                for value in metadata[col].unique():
                    if pd.isna(value):
                        continue
                    mask = metadata[col] == value
                    indices = np.where(mask)[0]
                    
                    # Connect all pairs in this group
                    for i in range(len(indices)):
                        for j in range(i + 1, len(indices)):
                            idx_i, idx_j = indices[i], indices[j]
                            adjacency[idx_i, idx_j] += 1
                            adjacency[idx_j, idx_i] += 1
            else:
                # Numerical: use similarity based on normalized distance
                values = metadata[col].values
                if np.isnan(values).all():
                    continue
                    
                # Normalize
                values = (values - np.nanmin(values)) / (np.nanmax(values) - np.nanmin(values) + 1e-10)
                
                # Add similarity for nearby values
                for i in range(n_samples):
                    for j in range(i + 1, n_samples):
                        if not (np.isnan(values[i]) or np.isnan(values[j])):
                            sim = 1 - abs(values[i] - values[j])
                            if sim > 0.8:  # Only strong similarity
                                adjacency[i, j] += sim
                                adjacency[j, i] += sim
        
        # Normalize
        max_val = adjacency.max()
        if max_val > 0:
            adjacency = adjacency / max_val
        
        return adjacency.tocsr()
    
    def build_multiview_graph(
        self,
        semantic_embeddings: np.ndarray,
        lexical_matrix: csr_matrix | None = None,
        metadata_graph: csr_matrix | None = None,
        weights: dict[str, float] | None = None,
    ) -> "igraph.Graph":
        """
        Build combined multi-view graph.
        
        Fuses semantic, lexical, and metadata views into a single graph
        for robust community detection.
        
        Parameters
        ----------
        semantic_embeddings : np.ndarray
            Document embeddings.
        lexical_matrix : csr_matrix, optional
            TF-IDF matrix for lexical view.
        metadata_graph : csr_matrix, optional
            Pre-computed metadata adjacency.
        weights : dict, optional
            Weights for each view. Keys: "semantic", "lexical", "metadata"
            
        Returns
        -------
        graph : igraph.Graph
            Combined weighted graph.
        """
        import igraph as ig
        
        weights = weights or {"semantic": 0.5, "lexical": 0.3, "metadata": 0.2}
        n_samples = semantic_embeddings.shape[0]
        
        # Build semantic graph
        if self.graph_type == "knn":
            semantic_adj = self.build_knn_graph(semantic_embeddings)
        elif self.graph_type == "mutual_knn":
            semantic_adj = self.build_mutual_knn_graph(semantic_embeddings)
        elif self.graph_type == "snn":
            semantic_adj = self.build_snn_graph(semantic_embeddings)
        else:  # hybrid
            semantic_adj = self.build_hybrid_graph(semantic_embeddings)
        
        # Normalize
        if semantic_adj.max() > 0:
            semantic_adj = semantic_adj / semantic_adj.max()
        
        # Start with semantic
        combined_adj = weights["semantic"] * semantic_adj
        
        # Add lexical if available
        if lexical_matrix is not None and weights.get("lexical", 0) > 0:
            lexical_adj = self.build_lexical_graph(lexical_matrix)
            if lexical_adj.max() > 0:
                lexical_adj = lexical_adj / lexical_adj.max()
            combined_adj = combined_adj + weights["lexical"] * lexical_adj
        
        # Add metadata if available
        if metadata_graph is not None and weights.get("metadata", 0) > 0:
            if metadata_graph.max() > 0:
                metadata_graph = metadata_graph / metadata_graph.max()
            combined_adj = combined_adj + weights["metadata"] * metadata_graph
        
        # Convert to igraph
        combined_adj = combined_adj.tocoo()
        
        edges = list(zip(combined_adj.row, combined_adj.col))
        weights_list = combined_adj.data.tolist()
        
        # Remove duplicate edges (keep max weight)
        edge_weights = {}
        for (i, j), w in zip(edges, weights_list):
            key = (min(i, j), max(i, j))
            if key not in edge_weights or w > edge_weights[key]:
                edge_weights[key] = w
        
        edges = list(edge_weights.keys())
        weights_list = list(edge_weights.values())
        
        # Create graph
        graph = ig.Graph(n=n_samples, edges=edges, directed=False)
        graph.es["weight"] = weights_list
        
        return graph
    
    def get_feature_names(self) -> list[str]:
        """Get TF-IDF feature names (for keyword extraction)."""
        if hasattr(self._tfidf_vectorizer, "get_feature_names_out"):
            return list(self._tfidf_vectorizer.get_feature_names_out())
        return list(self._tfidf_vectorizer.get_feature_names())
