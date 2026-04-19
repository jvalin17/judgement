"""k-Nearest Neighbors classifier using only Python stdlib.

Stores labeled examples and predicts by majority vote of the K closest
neighbors, weighted by inverse distance.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional, Tuple

from backend.app.ml.data_store import get_default_store

logger = logging.getLogger(__name__)

# Default number of neighbors to consider
DEFAULT_K = 5

# Minimum examples needed before predictions are used
MIN_EXAMPLES = 10

# Small constant to avoid division by zero in weighted voting
_DISTANCE_EPSILON = 1e-6


def _euclidean_distance(point_a: List[float], point_b: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(point_a, point_b)))


def _find_neighbors(
    query: List[float],
    examples: List[dict],
    k: int,
) -> List[Tuple[dict, float]]:
    """Find k nearest neighbors by Euclidean distance."""
    distances = []
    for example in examples:
        dist = _euclidean_distance(query, example["features"])
        distances.append((example, dist))
    distances.sort(key=lambda pair: pair[1])
    return distances[:k]


def predict_bid(
    query_features: List[float],
    data_file: str,
    k: int = DEFAULT_K,
) -> Optional[int]:
    """Predict a bid amount from stored winner bid decisions.

    Returns None if not enough data for a confident prediction.
    """
    examples = get_default_store().load_examples(data_file)
    if len(examples) < MIN_EXAMPLES:
        logger.debug("Insufficient bid data (%d < %d), skipping prediction", len(examples), MIN_EXAMPLES)
        return None

    neighbors = _find_neighbors(query_features, examples, k)
    if not neighbors:
        return None

    return _weighted_vote_numeric(neighbors)


def predict_card_index(
    query_features: List[float],
    num_valid_cards: int,
    data_file: str,
    k: int = DEFAULT_K,
) -> Optional[int]:
    """Predict which card to play (as index into sorted valid cards).

    Returns None if not enough data for a confident prediction.
    """
    examples = get_default_store().load_examples(data_file)
    if len(examples) < MIN_EXAMPLES:
        logger.debug("Insufficient play data (%d < %d), skipping prediction", len(examples), MIN_EXAMPLES)
        return None

    neighbors = _find_neighbors(query_features, examples, k)
    if not neighbors:
        return None

    predicted_index = _weighted_vote_numeric(neighbors)
    return max(0, min(predicted_index, num_valid_cards - 1))


def _weighted_vote_numeric(neighbors: List[Tuple[dict, float]]) -> int:
    """Weighted average of neighbor labels, rounded to nearest int."""
    weighted_sum = 0.0
    weight_total = 0.0

    for example, distance in neighbors:
        weight = 1.0 / (distance + _DISTANCE_EPSILON)
        weighted_sum += weight * example["label"]
        weight_total += weight

    if weight_total == 0:
        return round(neighbors[0][0]["label"])

    return round(weighted_sum / weight_total)


def append_example(
    data_file: str,
    features: List[float],
    label: float,
    metadata: Optional[dict] = None,
) -> None:
    """Append a single labeled example to the data file (JSONL format)."""
    get_default_store().append_example(data_file, features, label, metadata)


def example_count(data_file: str) -> int:
    """Count examples in a data file without loading all into memory."""
    return get_default_store().example_count(data_file)
