"""k-Nearest Neighbors classifier with normalization, confidence, and outcome weighting.

CardGameKNN encapsulates the full prediction pipeline:
  1. Min-max feature normalization (auto-padded for mixed-dimension data)
  2. Euclidean distance on normalized features
  3. Weighted voting with winner/loser outcome awareness
  4. Confidence scoring (distance × agreement) with threshold fallback

The class is self-contained — swap it for a different algorithm by matching
the predict() interface.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Dict, List, Optional, Tuple

from backend.app.ml.data_store import get_default_store

logger = logging.getLogger(__name__)

# --- Prediction result ---

class Prediction:
    """A prediction with value and confidence score."""
    __slots__ = ("value", "confidence")

    def __init__(self, value: int, confidence: float):
        self.value = value
        self.confidence = confidence


# --- CardGameKNN ---

class CardGameKNN:
    """kNN classifier with normalization, confidence, and outcome weighting."""

    def __init__(
        self,
        k: int = 7,
        min_examples: int = 10,
        max_examples: int = 5000,
        confidence_threshold: float = 0.25,
        loser_weight: float = -0.3,
    ):
        self._k = k
        self._min_examples = min_examples
        self._max_examples = max_examples
        self._confidence_threshold = confidence_threshold
        self._loser_weight = loser_weight

        # Cached normalization stats: list of (min, max) per feature
        self._norm_stats: Optional[List[Tuple[float, float]]] = None
        self._norm_count: int = 0

    # --- Public API ---

    def predict(
        self,
        features: List[float],
        examples: List[dict],
    ) -> Optional[Prediction]:
        """Predict a label from examples. Returns None if insufficient data or low confidence."""
        if len(examples) < self._min_examples:
            return None

        num_dims = len(features)
        self._maybe_refit_normalizer(examples, num_dims)

        norm_query = self._normalize(features)
        norm_examples = self._normalize_examples(examples, num_dims)

        neighbors = self._find_neighbors(norm_query, norm_examples)
        if not neighbors:
            return None

        confidence = self._compute_confidence(neighbors)
        if confidence < self._confidence_threshold:
            logger.debug("Low confidence %.3f (threshold %.3f), skipping",
                         confidence, self._confidence_threshold)
            return None

        value = self._weighted_vote(neighbors)
        return Prediction(value=value, confidence=confidence)

    def fit_normalizer(self, examples: List[dict], num_dims: int) -> None:
        """Compute min-max stats from examples."""
        if not examples:
            self._norm_stats = [(0.0, 1.0)] * num_dims
            self._norm_count = 0
            return

        mins = [float("inf")] * num_dims
        maxs = [float("-inf")] * num_dims

        for example in examples:
            feats = example["features"]
            for index in range(min(len(feats), num_dims)):
                if feats[index] < mins[index]:
                    mins[index] = feats[index]
                if feats[index] > maxs[index]:
                    maxs[index] = feats[index]

        # For dimensions not covered by shorter old records, keep defaults
        for index in range(num_dims):
            if mins[index] == float("inf"):
                mins[index] = 0.0
                maxs[index] = 1.0

        self._norm_stats = list(zip(mins, maxs))
        self._norm_count = len(examples)

    # --- Internals ---

    def _maybe_refit_normalizer(self, examples: List[dict], num_dims: int) -> None:
        """Refit normalizer if dataset grew by 20% or dimensions changed."""
        if (self._norm_stats is None
                or len(self._norm_stats) != num_dims
                or len(examples) > self._norm_count * 1.2):
            self.fit_normalizer(examples, num_dims)

    def _normalize(self, features: List[float]) -> List[float]:
        """Normalize a single feature vector to [0, 1] using cached stats."""
        if not self._norm_stats:
            return features
        result = []
        for index, value in enumerate(features):
            if index < len(self._norm_stats):
                lo, hi = self._norm_stats[index]
                if hi - lo > 1e-9:
                    result.append((value - lo) / (hi - lo))
                else:
                    result.append(0.5)
            else:
                result.append(0.5)
        return result

    def _normalize_examples(
        self, examples: List[dict], num_dims: int,
    ) -> List[Tuple[List[float], float, float]]:
        """Normalize all examples, pad shorter ones, extract outcome weight.

        Returns list of (normalized_features, label, outcome_weight).
        """
        result = []
        for example in examples:
            feats = example["features"]
            # Pad shorter old records with 0.5 (normalized midpoint)
            padded = list(feats) + [0.5] * max(0, num_dims - len(feats))
            padded = padded[:num_dims]
            norm_feats = self._normalize(padded)

            outcome = example.get("outcome", "win")
            outcome_weight = 1.0 if outcome == "win" else self._loser_weight

            result.append((norm_feats, example["label"], outcome_weight))
        return result

    def _find_neighbors(
        self,
        query: List[float],
        examples: List[Tuple[List[float], float, float]],
    ) -> List[Tuple[float, float, float]]:
        """Find k nearest neighbors. Returns list of (distance, label, outcome_weight)."""
        pool = examples
        if len(pool) > self._max_examples:
            pool = random.sample(pool, self._max_examples)

        distances: List[Tuple[float, float, float]] = []
        for norm_feats, label, outcome_weight in pool:
            dist = _euclidean_distance(query, norm_feats)
            distances.append((dist, label, outcome_weight))

        distances.sort(key=lambda triple: triple[0])
        return distances[:self._k]

    def _compute_confidence(
        self, neighbors: List[Tuple[float, float, float]],
    ) -> float:
        """Confidence from distance closeness × label agreement."""
        distances = [dist for dist, _, _ in neighbors]
        labels = [label for _, label, _ in neighbors]

        mean_dist = sum(distances) / len(distances) if distances else 1.0
        dist_confidence = 1.0 / (1.0 + mean_dist)

        mean_label = sum(labels) / len(labels) if labels else 0.0
        label_variance = (
            sum((label - mean_label) ** 2 for label in labels) / len(labels)
            if labels else 1.0
        )
        agree_confidence = 1.0 / (1.0 + label_variance)

        return dist_confidence * agree_confidence

    def _weighted_vote(
        self, neighbors: List[Tuple[float, float, float]],
    ) -> int:
        """Outcome-aware weighted vote. Winners add weight, losers subtract."""
        label_scores: Dict[int, float] = {}

        for distance, label, outcome_weight in neighbors:
            inv_dist = 1.0 / (distance + 1e-6)
            rounded_label = round(label)
            weight = inv_dist * outcome_weight
            label_scores[rounded_label] = label_scores.get(rounded_label, 0.0) + weight

        if not label_scores:
            return round(neighbors[0][1])

        # Pick label with highest net score (filter out net-negative labels)
        best_label = max(label_scores, key=lambda lbl: label_scores[lbl])
        if label_scores[best_label] <= 0:
            # All labels net-negative — no useful prediction
            return round(neighbors[0][1])
        return best_label


# --- Module-level helpers (Euclidean) ---

def _euclidean_distance(point_a: List[float], point_b: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(point_a, point_b)))


# --- Module-level singleton + backward-compatible API ---

# Constants re-exported for backward compatibility with tests
DEFAULT_K = 7
MIN_EXAMPLES = 10
MAX_KNN_EXAMPLES = 5000

_knn = CardGameKNN()


def _find_neighbors(
    query: List[float],
    examples: List[dict],
    k: int = DEFAULT_K,
) -> List[Tuple[dict, float]]:
    """Backward-compatible wrapper. Returns list of (example, distance)."""
    pool = examples
    if len(pool) > MAX_KNN_EXAMPLES:
        pool = random.sample(pool, MAX_KNN_EXAMPLES)
    distances = []
    for example in pool:
        dist = _euclidean_distance(query, example["features"])
        distances.append((example, dist))
    distances.sort(key=lambda pair: pair[1])
    return distances[:k]


def _weighted_vote_numeric(neighbors: List[Tuple[dict, float]]) -> int:
    """Backward-compatible wrapper. Weighted average of neighbor labels."""
    weighted_sum = 0.0
    weight_total = 0.0
    for example, distance in neighbors:
        weight = 1.0 / (distance + 1e-6)
        weighted_sum += weight * example["label"]
        weight_total += weight
    if weight_total == 0:
        return round(neighbors[0][0]["label"])
    return round(weighted_sum / weight_total)


def predict_bid(
    query_features: List[float],
    data_file: str,
    k: int = 7,
) -> Optional[int]:
    """Predict a bid amount. Returns None if not enough data or low confidence."""
    examples = get_default_store().load_examples(data_file)
    prediction = _knn.predict(query_features, examples)
    return prediction.value if prediction else None


def predict_card_index(
    query_features: List[float],
    num_valid_cards: int,
    data_file: str,
    k: int = 7,
) -> Optional[int]:
    """Predict which card to play. Returns None if not enough data or low confidence."""
    examples = get_default_store().load_examples(data_file)
    prediction = _knn.predict(query_features, examples)
    if prediction is None:
        return None
    return max(0, min(prediction.value, num_valid_cards - 1))


def append_example(
    data_file: str,
    features: List[float],
    label: float,
    metadata: Optional[dict] = None,
) -> None:
    """Append a single labeled example to the data file."""
    get_default_store().append_example(data_file, features, label, metadata)


def example_count(data_file: str) -> int:
    """Count examples in a data file."""
    return get_default_store().example_count(data_file)
