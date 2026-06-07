from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class OrbitalImageAnalysis:
    water_percent: float
    vegetation_percent: float
    exposed_soil_percent: float
    affected_area_percent: float
    environmental_risk: float
    processed_image_rgb: np.ndarray
    mask_image_rgb: np.ndarray

    def as_dict(self) -> dict[str, float]:
        return {
            "water_percent": self.water_percent,
            "vegetation_percent": self.vegetation_percent,
            "exposed_soil_percent": self.exposed_soil_percent,
            "affected_area_percent": self.affected_area_percent,
            "environmental_risk": self.environmental_risk,
        }


def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Imagem orbital inválida ou em formato não suportado.")
    return image


def load_image_from_file(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Não foi possível ler a imagem orbital: {path}")
    return image


def analyze_image_file(path: str | Path) -> OrbitalImageAnalysis:
    return analyze_image_array(load_image_from_file(path))


def analyze_image_array(image_bgr: np.ndarray) -> OrbitalImageAnalysis:
    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("Imagem orbital vazia.")

    resized = _fit_image(image_bgr)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)

    water_mask = _clean_mask(
        cv2.inRange(hsv, np.array([85, 35, 25]), np.array([135, 255, 235]))
    )
    vegetation_mask = _clean_mask(
        cv2.inRange(hsv, np.array([35, 30, 25]), np.array([90, 255, 245]))
    )
    soil_mask = _clean_mask(
        cv2.inRange(hsv, np.array([5, 35, 45]), np.array([32, 255, 245]))
    )

    water_percent = _mask_percent(water_mask)
    vegetation_percent = _mask_percent(vegetation_mask)
    exposed_soil_percent = _mask_percent(soil_mask)

    low_vegetation_pressure = max(0.0, 55.0 - vegetation_percent)
    affected_area_percent = _round_score(
        water_percent * 1.20 + exposed_soil_percent * 0.65 + low_vegetation_pressure * 0.20
    )
    environmental_risk = _round_score(
        water_percent * 1.35 + exposed_soil_percent * 0.85 + low_vegetation_pressure * 0.35
    )

    mask_rgb = _build_mask_image(water_mask, vegetation_mask, soil_mask)
    processed_rgb = _blend_overlay(resized, mask_rgb)

    return OrbitalImageAnalysis(
        water_percent=water_percent,
        vegetation_percent=vegetation_percent,
        exposed_soil_percent=exposed_soil_percent,
        affected_area_percent=affected_area_percent,
        environmental_risk=environmental_risk,
        processed_image_rgb=processed_rgb,
        mask_image_rgb=mask_rgb,
    )


def save_processed_image(analysis: OrbitalImageAnalysis, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), cv2.cvtColor(analysis.processed_image_rgb, cv2.COLOR_RGB2BGR))
    return output


def _fit_image(image_bgr: np.ndarray, max_side: int = 960) -> np.ndarray:
    height, width = image_bgr.shape[:2]
    scale = min(1.0, max_side / max(height, width))
    if scale == 1.0:
        return image_bgr.copy()
    return cv2.resize(image_bgr, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)


def _clean_mask(mask: np.ndarray) -> np.ndarray:
    kernel = np.ones((5, 5), np.uint8)
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)


def _mask_percent(mask: np.ndarray) -> float:
    return round(float(np.count_nonzero(mask)) / float(mask.size) * 100.0, 1)


def _round_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 1)


def _build_mask_image(water_mask: np.ndarray, vegetation_mask: np.ndarray, soil_mask: np.ndarray) -> np.ndarray:
    mask_rgb = np.zeros((*water_mask.shape, 3), dtype=np.uint8)
    mask_rgb[vegetation_mask > 0] = (46, 125, 50)
    mask_rgb[soil_mask > 0] = (191, 126, 41)
    mask_rgb[water_mask > 0] = (30, 104, 210)
    return mask_rgb


def _blend_overlay(image_bgr: np.ndarray, mask_rgb: np.ndarray) -> np.ndarray:
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    colored_pixels = np.any(mask_rgb > 0, axis=2)
    overlay = image_rgb.copy()
    overlay[colored_pixels] = cv2.addWeighted(
        image_rgb[colored_pixels],
        0.48,
        mask_rgb[colored_pixels],
        0.52,
        0,
    )
    return overlay

