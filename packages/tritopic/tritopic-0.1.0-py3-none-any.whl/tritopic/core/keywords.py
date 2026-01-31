"""
Keyword Extraction for TriTopic
================================

Extract representative keywords for topics using:
- c-TF-IDF (class-based TF-IDF, like BERTopic)
- BM25 scoring
- KeyBERT (embedding-based)
"""

from __future__ import annotations

from typing import Literal
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


class KeywordExtractor:
    """
    Extract keywords for topics.
    
    Supports multiple extraction methods for flexibility.
    
    Parameters
    ----------
    method : str
        Extraction method: "ctfidf", "bm25", or "keybert"
    n_keywords : int
        Number of keywords to extract per topic. Default: 10
    ngram_range : tuple
        N-gram range for keyword extraction. Default: (1, 2)
    """
    
    def __init__(
        self,
        method: Literal["ctfidf", "bm25", "keybert"] = "ctfidf",
        n_keywords: int = 10,
        ngram_range: tuple[int, int] = (1, 2),
        min_df: int = 2,
        max_df: float = 0.95,
    ):
        self.method = method
        self.n_keywords = n_keywords
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        
        self._vectorizer = None
        self._vocabulary = None
    
    def extract(
        self,
        topic_docs: list[str],
        all_docs: list[str] | None = None,
        n_keywords: int | None = None,
    ) -> tuple[list[str], list[float]]:
        """
        Extract keywords from topic documents.
        
        Parameters
        ----------
        topic_docs : list[str]
            Documents belonging to the topic.
        all_docs : list[str], optional
            All documents in corpus (needed for c-TF-IDF).
        n_keywords : int, optional
            Override default n_keywords.
            
        Returns
        -------
        keywords : list[str]
            Top keywords for the topic.
        scores : list[float]
            Keyword scores.
        """
        n = n_keywords or self.n_keywords
        
        if self.method == "ctfidf":
            return self._extract_ctfidf(topic_docs, all_docs or topic_docs, n)
        elif self.method == "bm25":
            return self._extract_bm25(topic_docs, all_docs or topic_docs, n)
        elif self.method == "keybert":
            return self._extract_keybert(topic_docs, n)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _extract_ctfidf(
        self,
        topic_docs: list[str],
        all_docs: list[str],
        n_keywords: int,
    ) -> tuple[list[str], list[float]]:
        """
        Extract keywords using class-based TF-IDF (c-TF-IDF).
        
        c-TF-IDF treats all documents in a topic as a single "class document"
        and computes TF-IDF against the corpus. This highlights words that
        are distinctive for the topic.
        """
        # Fit vectorizer on all docs if not already
        if self._vectorizer is None:
            self._vectorizer = CountVectorizer(
                ngram_range=self.ngram_range,
                stop_words="english",
                min_df=self.min_df,
                max_df=self.max_df,
            )
            self._vectorizer.fit(all_docs)
            self._vocabulary = self._vectorizer.get_feature_names_out()
        
        # Concatenate topic docs into a single "class document"
        topic_text = " ".join(topic_docs)
        
        # Get term frequencies for topic
        topic_tf = self._vectorizer.transform([topic_text]).toarray()[0]
        
        # Get term frequencies across all docs
        all_tf = self._vectorizer.transform(all_docs).toarray()
        
        # Compute IDF: log(N / (1 + df))
        doc_freq = np.sum(all_tf > 0, axis=0)
        idf = np.log(len(all_docs) / (1 + doc_freq))
        
        # c-TF-IDF = TF * IDF (with smoothing)
        topic_tf_normalized = topic_tf / (topic_tf.sum() + 1e-10)
        ctfidf_scores = topic_tf_normalized * idf
        
        # Get top keywords
        top_indices = np.argsort(ctfidf_scores)[::-1][:n_keywords]
        
        keywords = [self._vocabulary[i] for i in top_indices]
        scores = [float(ctfidf_scores[i]) for i in top_indices]
        
        return keywords, scores
    
    def _extract_bm25(
        self,
        topic_docs: list[str],
        all_docs: list[str],
        n_keywords: int,
    ) -> tuple[list[str], list[float]]:
        """
        Extract keywords using BM25 scoring.
        
        BM25 is more robust to document length variations than TF-IDF.
        """
        from rank_bm25 import BM25Okapi
        
        # Tokenize
        def tokenize(text):
            # Simple tokenization
            import re
            tokens = re.findall(r'\b\w+\b', text.lower())
            # Remove stopwords
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
                'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
                'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                'this', 'that', 'these', 'those', 'it', 'its', 'as', 'if', 'then',
            }
            return [t for t in tokens if t not in stopwords and len(t) > 2]
        
        # Tokenize all docs
        tokenized_all = [tokenize(doc) for doc in all_docs]
        tokenized_topic = [tokenize(doc) for doc in topic_docs]
        
        # Build vocabulary from topic docs
        topic_vocab = Counter()
        for tokens in tokenized_topic:
            topic_vocab.update(tokens)
        
        # Fit BM25 on all docs
        bm25 = BM25Okapi(tokenized_all)
        
        # Score each word in topic vocabulary
        word_scores = {}
        for word, freq in topic_vocab.items():
            # Use word as query
            scores = bm25.get_scores([word])
            
            # Average score weighted by frequency in topic
            avg_score = np.mean(scores)
            word_scores[word] = avg_score * np.log1p(freq)
        
        # Sort by score
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        keywords = [w for w, s in sorted_words[:n_keywords]]
        scores = [s for w, s in sorted_words[:n_keywords]]
        
        # Normalize scores
        max_score = max(scores) if scores else 1
        scores = [s / max_score for s in scores]
        
        return keywords, scores
    
    def _extract_keybert(
        self,
        topic_docs: list[str],
        n_keywords: int,
    ) -> tuple[list[str], list[float]]:
        """
        Extract keywords using KeyBERT (embedding-based).
        
        KeyBERT finds keywords by comparing candidate embeddings
        to the document embedding.
        """
        from keybert import KeyBERT
        
        # Concatenate topic docs
        topic_text = " ".join(topic_docs)
        
        # Initialize KeyBERT
        kw_model = KeyBERT()
        
        # Extract keywords
        keywords_with_scores = kw_model.extract_keywords(
            topic_text,
            keyphrase_ngram_range=self.ngram_range,
            stop_words="english",
            top_n=n_keywords,
            use_mmr=True,  # Maximal Marginal Relevance for diversity
            diversity=0.5,
        )
        
        keywords = [kw for kw, score in keywords_with_scores]
        scores = [float(score) for kw, score in keywords_with_scores]
        
        return keywords, scores
    
    def extract_all_topics(
        self,
        documents: list[str],
        labels: np.ndarray,
        n_keywords: int | None = None,
    ) -> dict[int, tuple[list[str], list[float]]]:
        """
        Extract keywords for all topics at once.
        
        Parameters
        ----------
        documents : list[str]
            All documents.
        labels : np.ndarray
            Topic assignments.
        n_keywords : int, optional
            Override default n_keywords.
            
        Returns
        -------
        topic_keywords : dict
            Mapping from topic_id to (keywords, scores).
        """
        result = {}
        
        for topic_id in np.unique(labels):
            if topic_id == -1:
                continue
                
            mask = labels == topic_id
            topic_docs = [documents[i] for i in np.where(mask)[0]]
            
            keywords, scores = self.extract(topic_docs, documents, n_keywords)
            result[int(topic_id)] = (keywords, scores)
        
        return result


class KeyphraseExtractor:
    """
    Extract keyphrases (multi-word) using YAKE or TextRank.
    """
    
    def __init__(
        self,
        method: Literal["yake", "textrank"] = "yake",
        n_keyphrases: int = 10,
        max_ngram: int = 3,
    ):
        self.method = method
        self.n_keyphrases = n_keyphrases
        self.max_ngram = max_ngram
    
    def extract(self, text: str) -> list[tuple[str, float]]:
        """Extract keyphrases from text."""
        if self.method == "yake":
            return self._extract_yake(text)
        else:
            raise ValueError(f"Unknown method: {self.method}")
    
    def _extract_yake(self, text: str) -> list[tuple[str, float]]:
        """Extract using YAKE algorithm."""
        try:
            import yake
        except ImportError:
            # Fallback to simple extraction
            return self._simple_extract(text)
        
        kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=self.max_ngram,
            dedupLim=0.7,
            top=self.n_keyphrases,
            features=None,
        )
        
        keywords = kw_extractor.extract_keywords(text)
        
        # YAKE returns (keyword, score) where lower score is better
        # Invert for consistency
        max_score = max(s for _, s in keywords) if keywords else 1
        return [(kw, 1 - s/max_score) for kw, s in keywords]
    
    def _simple_extract(self, text: str) -> list[tuple[str, float]]:
        """Simple n-gram frequency extraction."""
        import re
        from collections import Counter
        
        # Tokenize
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Generate n-grams
        ngrams = []
        for n in range(1, self.max_ngram + 1):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i:i+n])
                ngrams.append(ngram)
        
        # Count and return top
        counts = Counter(ngrams)
        top = counts.most_common(self.n_keyphrases)
        
        max_count = top[0][1] if top else 1
        return [(phrase, count/max_count) for phrase, count in top]
