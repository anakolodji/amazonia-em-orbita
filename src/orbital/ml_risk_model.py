from __future__ import annotations

import math
from typing import Mapping


FEATURE_WEIGHTS = {
    "environmental_risk": 1.25,
    "sanitary_case_score": 1.10,
    "logistic_isolation": 0.85,
    "rainfall_intensity": 0.80,
    "orbital_area_affected": 0.70,
}
MODEL_BIAS = -2.45


def predict_ml_risk_score(features: Mapping[str, float]) -> float:
    linear = MODEL_BIAS
    for name, weight in FEATURE_WEIGHTS.items():
        linear += weight * _score(features[name])
    probability = 1.0 / (1.0 + math.exp(-linear))
    return round(probability * 100.0, 1)


def blend_ipho_with_ml(ipho: float, ml_risk_score: float) -> float:
    return round((float(ipho) * 0.75) + (float(ml_risk_score) * 0.25), 1)


def _score(value: float) -> float:
    return max(0.0, min(1.0, float(value) / 100.0))
