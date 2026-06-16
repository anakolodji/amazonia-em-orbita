from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DEFAULT_SENSOR_PATH = Path(__file__).resolve().parents[2] / "dados_sensores.jsonl"


@dataclass(frozen=True)
class SensorRiskSummary:
    latest_risk: str
    latest_score: float
    total_readings: int
    high_risk_readings: int


def load_sensor_readings(path: str | Path = DEFAULT_SENSOR_PATH, limit: int = 120) -> pd.DataFrame:
    sensor_path = Path(path)
    if not sensor_path.exists():
        return pd.DataFrame(columns=["timestamp", "temperatura", "umidade", "chuva", "risk_score", "risk_label"])

    rows = []
    for line in sensor_path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "temperatura", "umidade", "chuva", "risk_score", "risk_label"])

    for column in ["temperatura", "umidade", "chuva"]:
        if column not in df.columns:
            df[column] = 0.0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    if "timestamp" not in df.columns:
        df["timestamp"] = pd.NaT
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["risk_score"] = df.apply(_sensor_risk_score, axis=1)
    df["risk_label"] = df["risk_score"].map(_risk_label)
    return df.dropna(subset=["timestamp"]).reset_index(drop=True)


def summarize_sensor_risk(df: pd.DataFrame) -> SensorRiskSummary:
    if df.empty:
        return SensorRiskSummary("Sem dados", 0.0, 0, 0)
    latest = df.iloc[-1]
    high_risk = int((df["risk_label"] == "Alto").sum())
    return SensorRiskSummary(
        latest_risk=str(latest["risk_label"]),
        latest_score=float(latest["risk_score"]),
        total_readings=len(df),
        high_risk_readings=high_risk,
    )


def _sensor_risk_score(row) -> float:
    temp_score = 100.0 if 22 <= float(row["temperatura"]) <= 30 else 35.0
    humidity_score = min(100.0, max(0.0, float(row["umidade"])))
    rain_score = min(100.0, max(0.0, float(row["chuva"]) / 120.0 * 100.0))
    return round((temp_score * 0.30) + (humidity_score * 0.30) + (rain_score * 0.40), 1)


def _risk_label(score: float) -> str:
    if score >= 70:
        return "Alto"
    if score >= 45:
        return "Médio"
    return "Baixo"
