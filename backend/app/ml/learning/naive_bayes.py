"""Gaussian Naive Bayes classifier — stdlib only.

Computes per-label mean/variance for each feature, predicts via
log-space posterior probabilities. Naturally outputs calibrated
confidence scores.
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

from backend.app.ml.learning.model_base import Prediction

logger = logging.getLogger(__name__)

MIN_EXAMPLES_PER_LABEL = 3
CONFIDENCE_THRESHOLD = 0.3
VARIANCE_SMOOTHING = 1e-6


class NaiveBayesModel:
    """Gaussian Naive Bayes with Laplace-smoothed variance."""

    @property
    def model_name(self) -> str:
        return "naive_bayes"

    def __init__(self):
        # label -> {"count": int, "means": [float], "variances": [float]}
        self._stats: Optional[Dict[int, dict]] = None
        self._total: int = 0
        self._fit_count: int = 0

    def predict(
        self,
        features: List[float],
        examples: List[dict],
        context: Optional[Dict] = None,
    ) -> Optional[Prediction]:
        winners = [ex for ex in examples if ex.get("outcome", "win") == "win"]
        if len(winners) < MIN_EXAMPLES_PER_LABEL * 2:
            return None

        self._maybe_refit(winners, len(features))
        if not self._stats:
            return None

        posteriors = self._compute_posteriors(features)
        if not posteriors:
            return None

        best_label = max(posteriors, key=lambda lbl: posteriors[lbl])
        total_log = _logsumexp(list(posteriors.values()))
        confidence = math.exp(posteriors[best_label] - total_log)

        if confidence < CONFIDENCE_THRESHOLD:
            return None
        return Prediction(value=best_label, confidence=confidence)

    def _maybe_refit(self, winners: List[dict], num_dims: int) -> None:
        if self._stats is not None and len(winners) <= self._fit_count * 1.2:
            return
        self._fit(winners, num_dims)

    def _fit(self, examples: List[dict], num_dims: int) -> None:
        label_data: Dict[int, List[List[float]]] = {}
        for ex in examples:
            label = round(ex["label"])
            feats = list(ex["features"])
            feats.extend([0.0] * max(0, num_dims - len(feats)))
            feats = feats[:num_dims]
            label_data.setdefault(label, []).append(feats)

        self._stats = {}
        self._total = 0
        for label, rows in label_data.items():
            if len(rows) < MIN_EXAMPLES_PER_LABEL:
                continue
            count = len(rows)
            means = [sum(row[dim] for row in rows) / count for dim in range(num_dims)]
            variances = [
                sum((row[dim] - means[dim]) ** 2 for row in rows) / count + VARIANCE_SMOOTHING
                for dim in range(num_dims)
            ]
            self._stats[label] = {"count": count, "means": means, "variances": variances}
            self._total += count
        self._fit_count = sum(s["count"] for s in self._stats.values()) if self._stats else 0

    def _compute_posteriors(self, features: List[float]) -> Dict[int, float]:
        if not self._stats or self._total == 0:
            return {}

        posteriors: Dict[int, float] = {}
        for label, stats in self._stats.items():
            log_prior = math.log(stats["count"] / self._total)
            log_likelihood = 0.0
            for dim in range(min(len(features), len(stats["means"]))):
                log_likelihood += _gaussian_log_prob(
                    features[dim], stats["means"][dim], stats["variances"][dim],
                )
            posteriors[label] = log_prior + log_likelihood
        return posteriors


def _gaussian_log_prob(x: float, mean: float, variance: float) -> float:
    """Log of Gaussian PDF."""
    return -0.5 * (math.log(2 * math.pi * variance) + (x - mean) ** 2 / variance)


def _logsumexp(values: List[float]) -> float:
    """Numerically stable log(sum(exp(values)))."""
    if not values:
        return float("-inf")
    max_val = max(values)
    return max_val + math.log(sum(math.exp(v - max_val) for v in values))
