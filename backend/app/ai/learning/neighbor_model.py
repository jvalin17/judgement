"""k-Nearest Neighbors classifier using only Python stdlib.

Stores labeled examples and predicts by majority vote of the K closest
neighbors, weighted by inverse distance.
"""

from __future__ import annotations

import json
import math
import os
from typing import List, Optional, Tuple

# Default number of neighbors to consider
DEFAULT_K = 5

# Minimum examples needed before predictions are used
MIN_EXAMPLES = 10


def _euclidean_distance(point_a: List[float], point_b: List[float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(point_a, point_b)))


def _find_neighbors(
    query: List[float],
    examples: List[dict],
    k: int,
) -> List[Tuple[dict, float]]:
    """Find k nearest neighbors by Euclidean distance.

    Returns list of (example, distance) tuples, sorted by distance.
    """
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
    examples = _load_examples(data_file)
    if len(examples) < MIN_EXAMPLES:
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
    examples = _load_examples(data_file)
    if len(examples) < MIN_EXAMPLES:
        return None

    neighbors = _find_neighbors(query_features, examples, k)
    if not neighbors:
        return None

    predicted_index = _weighted_vote_numeric(neighbors)
    # Clamp to valid range (different games may have different valid card counts)
    return max(0, min(predicted_index, num_valid_cards - 1))


def _weighted_vote_numeric(neighbors: List[Tuple[dict, float]]) -> int:
    """Weighted average of neighbor labels, rounded to nearest int.

    Weight = 1 / (distance + epsilon) to avoid division by zero.
    """
    epsilon = 1e-6
    weighted_sum = 0.0
    weight_total = 0.0

    for example, distance in neighbors:
        weight = 1.0 / (distance + epsilon)
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
    """Append a single labeled example to the data file (JSONL format).

    Optional metadata (e.g. strategy_type) is stored alongside but
    not used for predictions — only features and label are used by kNN.
    """
    directory = os.path.dirname(data_file)
    if directory:
        os.makedirs(directory, exist_ok=True)

    entry = {"features": features, "label": label}
    if metadata:
        entry.update(metadata)
    with open(data_file, "a") as file_handle:
        file_handle.write(json.dumps(entry) + "\n")


def _load_examples(data_file: str) -> List[dict]:
    """Load all examples from a JSONL file."""
    if not os.path.exists(data_file):
        return []

    examples = []
    with open(data_file, "r") as file_handle:
        for line in file_handle:
            line = line.strip()
            if line:
                try:
                    examples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return examples


def example_count(data_file: str) -> int:
    """Count examples in a data file without loading all into memory."""
    if not os.path.exists(data_file):
        return 0
    count = 0
    with open(data_file, "r") as file_handle:
        for line in file_handle:
            if line.strip():
                count += 1
    return count
