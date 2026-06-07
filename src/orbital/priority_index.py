from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import pandas as pd


IPHO_WEIGHTS = {
    "environmental_risk": 0.30,
    "sanitary_cases": 0.25,
    "logistic_isolation": 0.20,
    "rainfall_intensity": 0.15,
    "orbital_area_affected": 0.10,
}

SANITARY_CASE_REFERENCE = 160.0


@dataclass(frozen=True)
class PriorityInputs:
    environmental_risk: float
    sanitary_cases: float
    logistic_isolation: float
    rainfall_intensity: float
    orbital_area_affected: float


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def sanitary_cases_to_score(cases: float) -> float:
    return clamp_score(float(cases) / SANITARY_CASE_REFERENCE * 100.0)


def calculate_ipho(inputs: PriorityInputs | Mapping[str, float]) -> float:
    if isinstance(inputs, Mapping):
        values = PriorityInputs(
            environmental_risk=inputs["environmental_risk"],
            sanitary_cases=float(inputs.get("sanitary_cases", 0.0)),
            logistic_isolation=inputs["logistic_isolation"],
            rainfall_intensity=_mapping_value(inputs, "rainfall_intensity", "climate_intensity"),
            orbital_area_affected=inputs["orbital_area_affected"],
        )
        sanitary_score = _sanitary_score_from_mapping(inputs)
    else:
        values = inputs
        sanitary_score = sanitary_cases_to_score(values.sanitary_cases)

    score = (
        IPHO_WEIGHTS["environmental_risk"] * clamp_score(values.environmental_risk)
        + IPHO_WEIGHTS["sanitary_cases"] * sanitary_score
        + IPHO_WEIGHTS["logistic_isolation"] * clamp_score(values.logistic_isolation)
        + IPHO_WEIGHTS["rainfall_intensity"] * clamp_score(values.rainfall_intensity)
        + IPHO_WEIGHTS["orbital_area_affected"] * clamp_score(values.orbital_area_affected)
    )
    return round(score, 1)


def classify_priority(ipho: float) -> str:
    score = clamp_score(ipho)
    if score >= 70:
        return "Alta"
    if score >= 40:
        return "Média"
    return "Baixa"


def apply_priority_index(records: pd.DataFrame | Iterable[Mapping[str, object]]) -> pd.DataFrame:
    df = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    if df.empty:
        df["IPHO"] = []
        df["priority"] = []
        return df

    df["IPHO"] = df.apply(
        lambda row: calculate_ipho(row),
        axis=1,
    )
    df["sanitary_case_score"] = df.apply(_sanitary_score_from_mapping, axis=1)
    df["priority"] = df["IPHO"].map(classify_priority)
    return df.sort_values("IPHO", ascending=False).reset_index(drop=True)


def _mapping_value(inputs: Mapping[str, float], preferred: str, fallback: str) -> float:
    if preferred in inputs:
        return float(inputs[preferred])
    return float(inputs[fallback])


def _sanitary_score_from_mapping(inputs: Mapping[str, float]) -> float:
    if "sanitary_cases" in inputs:
        return sanitary_cases_to_score(inputs["sanitary_cases"])
    return clamp_score(inputs["sanitary_risk"])
