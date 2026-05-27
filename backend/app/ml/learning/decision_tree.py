"""Decision tree classifier using Gini impurity — stdlib only.

Builds a binary tree from game examples, caches it, and rebuilds when
the dataset grows by 20%. Excludes loser data from training.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple, Union

from backend.app.ml.learning.model_base import Prediction

logger = logging.getLogger(__name__)

MAX_DEPTH = 5
MIN_LEAF_SAMPLES = 5
CONFIDENCE_THRESHOLD = 0.4

# Type alias for tree nodes
TreeNode = Dict[str, Union[int, float, "TreeNode"]]


class DecisionTreeModel:
    """Decision tree with Gini splits, cached tree, loser exclusion."""

    @property
    def model_name(self) -> str:
        return "decision_tree"

    def __init__(self, max_depth: int = MAX_DEPTH, min_leaf: int = MIN_LEAF_SAMPLES):
        self._max_depth = max_depth
        self._min_leaf = min_leaf
        self._tree: Optional[TreeNode] = None
        self._tree_count: int = 0

    def predict(
        self,
        features: List[float],
        examples: List[dict],
        context: Optional[Dict] = None,
    ) -> Optional[Prediction]:
        if len(examples) < self._min_leaf * 2:
            return None

        self._maybe_rebuild(examples, len(features))
        if self._tree is None:
            return None

        leaf = self._traverse(self._tree, features)
        if leaf is None:
            return None

        label = leaf["label"]
        confidence = leaf["confidence"]
        if confidence < CONFIDENCE_THRESHOLD:
            return None
        return Prediction(value=int(label), confidence=confidence)

    def _maybe_rebuild(self, examples: List[dict], num_dims: int) -> None:
        winner_count = sum(1 for ex in examples if ex.get("outcome", "win") == "win")
        if self._tree is not None and winner_count <= self._tree_count * 1.2:
            return
        winners = self._filter_and_pad(examples, num_dims)
        if len(winners) < self._min_leaf * 2:
            self._tree = None
            return
        self._tree = self._build_tree(winners, depth=0)
        self._tree_count = len(winners)

    def _filter_and_pad(self, examples: List[dict], num_dims: int) -> List[Tuple[List[float], int]]:
        result = []
        for ex in examples:
            if ex.get("outcome", "win") != "win":
                continue
            feats = list(ex["features"])
            feats.extend([0.0] * max(0, num_dims - len(feats)))
            result.append((feats[:num_dims], round(ex["label"])))
        return result

    def _build_tree(self, data: List[Tuple[List[float], int]], depth: int) -> TreeNode:
        labels = [label for _, label in data]
        counts = Counter(labels)
        majority = counts.most_common(1)[0]
        confidence = majority[1] / len(labels)

        if depth >= self._max_depth or len(data) <= self._min_leaf or confidence == 1.0:
            return {"label": majority[0], "confidence": confidence, "leaf": True}

        best = self._best_split(data)
        if best is None:
            return {"label": majority[0], "confidence": confidence, "leaf": True}

        feature_idx, threshold, left_data, right_data = best
        if len(left_data) < self._min_leaf or len(right_data) < self._min_leaf:
            return {"label": majority[0], "confidence": confidence, "leaf": True}

        return {
            "feature": feature_idx,
            "threshold": threshold,
            "left": self._build_tree(left_data, depth + 1),
            "right": self._build_tree(right_data, depth + 1),
            "leaf": False,
        }

    def _best_split(self, data: List[Tuple[List[float], int]]) -> Optional[tuple]:
        num_dims = len(data[0][0])
        best_gini = float("inf")
        best_result = None

        for feature_idx in range(num_dims):
            values = sorted(set(feats[feature_idx] for feats, _ in data))
            if len(values) <= 1:
                continue
            candidates = values if len(values) <= 20 else values[::max(1, len(values) // 20)]

            for threshold in candidates:
                left = [(f, l) for f, l in data if f[feature_idx] <= threshold]
                right = [(f, l) for f, l in data if f[feature_idx] > threshold]
                if not left or not right:
                    continue

                weight_l = len(left) / len(data)
                weight_r = len(right) / len(data)
                gini = weight_l * self._gini([l for _, l in left]) + weight_r * self._gini([l for _, l in right])

                if gini < best_gini:
                    best_gini = gini
                    best_result = (feature_idx, threshold, left, right)

        return best_result

    @staticmethod
    def _gini(labels: List[int]) -> float:
        counts = Counter(labels)
        total = len(labels)
        if total == 0:
            return 0.0
        return 1.0 - sum((count / total) ** 2 for count in counts.values())

    def _traverse(self, node: TreeNode, features: List[float]) -> Optional[TreeNode]:
        if node.get("leaf"):
            return node
        feature_idx = node["feature"]
        if feature_idx >= len(features):
            return None
        if features[feature_idx] <= node["threshold"]:
            return self._traverse(node["left"], features)
        return self._traverse(node["right"], features)
