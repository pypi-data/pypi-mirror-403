"""
Consensus Leiden Clustering
============================

Robust community detection with:
- Leiden algorithm (better than Louvain)
- Consensus clustering for stability
- Resolution parameter tuning
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import adjusted_rand_score
from collections import Counter


class ConsensusLeiden:
    """
    Leiden clustering with consensus for stability.
    
    Runs multiple Leiden clusterings with different seeds and combines
    results using consensus clustering. This dramatically improves
    reproducibility and reduces sensitivity to random initialization.
    
    Parameters
    ----------
    resolution : float
        Resolution parameter for Leiden. Higher = more clusters. Default: 1.0
    n_runs : int
        Number of consensus runs. Default: 10
    random_state : int
        Random seed for reproducibility. Default: 42
    consensus_threshold : float
        Minimum agreement ratio for consensus. Default: 0.5
    """
    
    def __init__(
        self,
        resolution: float = 1.0,
        n_runs: int = 10,
        random_state: int = 42,
        consensus_threshold: float = 0.5,
    ):
        self.resolution = resolution
        self.n_runs = n_runs
        self.random_state = random_state
        self.consensus_threshold = consensus_threshold
        
        self.labels_: np.ndarray | None = None
        self.stability_score_: float | None = None
        self._all_partitions: list[np.ndarray] = []
    
    def fit_predict(
        self,
        graph: "igraph.Graph",
        min_cluster_size: int = 5,
        resolution: float | None = None,
    ) -> np.ndarray:
        """
        Fit Leiden clustering with consensus.
        
        Parameters
        ----------
        graph : igraph.Graph
            Input graph with edge weights.
        min_cluster_size : int
            Minimum cluster size. Smaller clusters become outliers.
        resolution : float, optional
            Override default resolution.
            
        Returns
        -------
        labels : np.ndarray
            Cluster assignments. -1 for outliers.
        """
        import leidenalg as la
        
        res = resolution or self.resolution
        n_nodes = graph.vcount()
        
        # Run multiple Leiden clusterings
        self._all_partitions = []
        
        for run in range(self.n_runs):
            seed = self.random_state + run
            
            # Run Leiden
            partition = la.find_partition(
                graph,
                la.RBConfigurationVertexPartition,
                weights="weight",
                resolution_parameter=res,
                seed=seed,
            )
            
            # Convert to labels
            labels = np.array(partition.membership)
            self._all_partitions.append(labels)
        
        # Compute consensus
        self.labels_ = self._compute_consensus(self._all_partitions)
        
        # Handle small clusters as outliers
        self.labels_ = self._handle_small_clusters(self.labels_, min_cluster_size)
        
        # Compute stability score
        self.stability_score_ = self._compute_stability()
        
        return self.labels_
    
    def _compute_consensus(self, partitions: list[np.ndarray]) -> np.ndarray:
        """
        Compute consensus partition from multiple runs.
        
        Uses co-occurrence matrix and hierarchical clustering.
        """
        n_nodes = len(partitions[0])
        n_runs = len(partitions)
        
        # Build co-occurrence matrix
        # co_occur[i,j] = fraction of runs where i and j are in same cluster
        co_occur = np.zeros((n_nodes, n_nodes))
        
        for partition in partitions:
            for cluster_id in np.unique(partition):
                members = np.where(partition == cluster_id)[0]
                for i in members:
                    for j in members:
                        co_occur[i, j] += 1
        
        co_occur /= n_runs
        
        # Convert co-occurrence to distance
        distance = 1 - co_occur
        
        # Hierarchical clustering on distance matrix
        # Use condensed form for linkage
        condensed = []
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                condensed.append(distance[i, j])
        condensed = np.array(condensed)
        
        # Average linkage tends to work well for consensus
        Z = linkage(condensed, method="average")
        
        # Cut at threshold that matches approximate number of clusters
        # from the most frequent partition
        n_clusters_list = [len(np.unique(p)) for p in partitions]
        median_n_clusters = int(np.median(n_clusters_list))
        
        # Find optimal cut
        best_labels = None
        best_score = -1
        
        for n_clusters in range(max(2, median_n_clusters - 2), median_n_clusters + 3):
            try:
                labels = fcluster(Z, n_clusters, criterion="maxclust")
                labels = labels - 1  # 0-indexed
                
                # Score by average ARI with original partitions
                ari_scores = [adjusted_rand_score(labels, p) for p in partitions]
                avg_ari = np.mean(ari_scores)
                
                if avg_ari > best_score:
                    best_score = avg_ari
                    best_labels = labels
            except Exception:
                continue
        
        if best_labels is None:
            # Fallback to most common partition
            best_labels = partitions[0]
        
        return best_labels
    
    def _handle_small_clusters(
        self,
        labels: np.ndarray,
        min_size: int,
    ) -> np.ndarray:
        """Mark small clusters as outliers (-1)."""
        result = labels.copy()
        
        for cluster_id in np.unique(labels):
            if cluster_id == -1:
                continue
            
            size = np.sum(labels == cluster_id)
            if size < min_size:
                result[labels == cluster_id] = -1
        
        # Relabel to consecutive integers
        unique_labels = sorted([l for l in np.unique(result) if l != -1])
        label_map = {old: new for new, old in enumerate(unique_labels)}
        label_map[-1] = -1
        
        result = np.array([label_map[l] for l in result])
        
        return result
    
    def _compute_stability(self) -> float:
        """Compute stability score as average pairwise ARI."""
        if len(self._all_partitions) < 2:
            return 1.0
        
        ari_scores = []
        for i in range(len(self._all_partitions)):
            for j in range(i + 1, len(self._all_partitions)):
                ari = adjusted_rand_score(
                    self._all_partitions[i],
                    self._all_partitions[j]
                )
                ari_scores.append(ari)
        
        return float(np.mean(ari_scores))
    
    def find_optimal_resolution(
        self,
        graph: "igraph.Graph",
        resolution_range: tuple[float, float] = (0.1, 2.0),
        n_steps: int = 10,
        target_n_topics: int | None = None,
    ) -> float:
        """
        Find optimal resolution parameter.
        
        Parameters
        ----------
        graph : igraph.Graph
            Input graph.
        resolution_range : tuple
            Range of resolutions to search.
        n_steps : int
            Number of resolutions to try.
        target_n_topics : int, optional
            If provided, find resolution closest to this number of topics.
            
        Returns
        -------
        optimal_resolution : float
            Best resolution parameter.
        """
        import leidenalg as la
        
        resolutions = np.linspace(resolution_range[0], resolution_range[1], n_steps)
        results = []
        
        for res in resolutions:
            partition = la.find_partition(
                graph,
                la.RBConfigurationVertexPartition,
                weights="weight",
                resolution_parameter=res,
                seed=self.random_state,
            )
            
            n_clusters = len(set(partition.membership))
            modularity = partition.modularity
            
            results.append({
                "resolution": res,
                "n_clusters": n_clusters,
                "modularity": modularity,
            })
        
        if target_n_topics is not None:
            # Find closest to target
            best = min(results, key=lambda x: abs(x["n_clusters"] - target_n_topics))
        else:
            # Find highest modularity
            best = max(results, key=lambda x: x["modularity"])
        
        return best["resolution"]


class HDBSCANClusterer:
    """
    Alternative clustering using HDBSCAN.
    
    Useful for datasets with varying density or many outliers.
    """
    
    def __init__(
        self,
        min_cluster_size: int = 10,
        min_samples: int = 5,
        metric: str = "euclidean",
    ):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.metric = metric
        
        self.labels_: np.ndarray | None = None
        self.probabilities_: np.ndarray | None = None
    
    def fit_predict(
        self,
        embeddings: np.ndarray,
        **kwargs,
    ) -> np.ndarray:
        """
        Fit HDBSCAN clustering.
        
        Parameters
        ----------
        embeddings : np.ndarray
            Document embeddings (optionally reduced with UMAP first).
            
        Returns
        -------
        labels : np.ndarray
            Cluster assignments. -1 for outliers.
        """
        import hdbscan
        
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            **kwargs,
        )
        
        self.labels_ = clusterer.fit_predict(embeddings)
        self.probabilities_ = clusterer.probabilities_
        
        return self.labels_
