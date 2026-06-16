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
    segmentation_confidence: float
    analysis_method: str
    processed_image_rgb: np.ndarray
    mask_image_rgb: np.ndarray

    def as_dict(self) -> dict[str, float]:
        return {
            "water_percent": self.water_percent,
            "vegetation_percent": self.vegetation_percent,
            "exposed_soil_percent": self.exposed_soil_percent,
            "affected_area_percent": self.affected_area_percent,
            "environmental_risk": self.environmental_risk,
            "segmentation_confidence": self.segmentation_confidence,
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

    hsv_water_mask = _clean_mask(
        cv2.inRange(hsv, np.array([85, 35, 25]), np.array([135, 255, 235]))
    )
    hsv_vegetation_mask = _clean_mask(
        cv2.inRange(hsv, np.array([35, 30, 25]), np.array([90, 255, 245]))
    )
    hsv_soil_mask = _clean_mask(
        cv2.inRange(hsv, np.array([5, 35, 45]), np.array([32, 255, 245]))
    )
    cluster_masks = _cluster_semantic_masks(resized)

    water_mask = _clean_mask(cv2.bitwise_or(hsv_water_mask, cluster_masks.water))
    vegetation_mask = _clean_mask(cv2.bitwise_or(hsv_vegetation_mask, cluster_masks.vegetation))
    soil_mask = _clean_mask(cv2.bitwise_or(hsv_soil_mask, cluster_masks.soil))

    water_percent = _mask_percent(water_mask)
    vegetation_percent = _mask_percent(vegetation_mask)
    exposed_soil_percent = _mask_percent(soil_mask)
    segmentation_confidence = _segmentation_confidence(water_mask, vegetation_mask, soil_mask)

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
        segmentation_confidence=segmentation_confidence,
        analysis_method="HSV + k-means não supervisionado",
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


@dataclass(frozen=True)
class _SemanticMasks:
    water: np.ndarray
    vegetation: np.ndarray
    soil: np.ndarray


def _cluster_semantic_masks(image_bgr: np.ndarray, max_side: int = 220) -> _SemanticMasks:
    small = _fit_image(image_bgr, max_side=max_side)
    pixels = small.reshape((-1, 3)).astype(np.float32)
    unique_colors = np.unique(pixels.astype(np.uint8), axis=0)
    cluster_count = max(1, min(5, len(unique_colors)))

    if cluster_count == 1:
        labels = np.zeros((small.shape[0] * small.shape[1], 1), dtype=np.int32)
        centers = unique_colors.astype(np.float32)
    else:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 24, 0.8)
        cv2.setRNGSeed(42)
        _, labels, centers = cv2.kmeans(
            pixels,
            cluster_count,
            None,
            criteria,
            3,
            cv2.KMEANS_PP_CENTERS,
        )

    centers_bgr = centers.astype(np.uint8).reshape(1, cluster_count, 3)
    centers_hsv = cv2.cvtColor(centers_bgr, cv2.COLOR_BGR2HSV)[0]
    labels_image = labels.reshape(small.shape[:2])

    water = np.zeros(small.shape[:2], dtype=np.uint8)
    vegetation = np.zeros(small.shape[:2], dtype=np.uint8)
    soil = np.zeros(small.shape[:2], dtype=np.uint8)

    for cluster_id, hsv_center in enumerate(centers_hsv):
        b, g, r = [float(channel) for channel in centers_bgr[0, cluster_id]]
        h, s, v = [float(channel) for channel in hsv_center]
        mask = labels_image == cluster_id

        if _looks_like_water(h, s, v, b, g, r):
            water[mask] = 255
        elif _looks_like_vegetation(h, s, v, b, g, r):
            vegetation[mask] = 255
        elif _looks_like_soil(h, s, v, b, g, r):
            soil[mask] = 255

    target_size = (image_bgr.shape[1], image_bgr.shape[0])
    return _SemanticMasks(
        water=cv2.resize(water, target_size, interpolation=cv2.INTER_NEAREST),
        vegetation=cv2.resize(vegetation, target_size, interpolation=cv2.INTER_NEAREST),
        soil=cv2.resize(soil, target_size, interpolation=cv2.INTER_NEAREST),
    )


def _looks_like_water(h: float, s: float, v: float, b: float, g: float, r: float) -> bool:
    hue_signal = 82 <= h <= 140 and s >= 25 and v >= 20
    channel_signal = b > g * 1.08 and b > r * 1.25
    return hue_signal or channel_signal


def _looks_like_vegetation(h: float, s: float, v: float, b: float, g: float, r: float) -> bool:
    hue_signal = 32 <= h <= 95 and s >= 25 and v >= 20
    channel_signal = g >= r * 1.08 and g >= b * 0.88
    return hue_signal or channel_signal


def _looks_like_soil(h: float, s: float, v: float, b: float, g: float, r: float) -> bool:
    hue_signal = 4 <= h <= 35 and s >= 25 and v >= 35
    channel_signal = r >= b * 1.08 and g >= b * 0.75 and s >= 20
    return hue_signal or channel_signal


def _segmentation_confidence(
    water_mask: np.ndarray,
    vegetation_mask: np.ndarray,
    soil_mask: np.ndarray,
) -> float:
    classified = np.any(
        np.stack([water_mask > 0, vegetation_mask > 0, soil_mask > 0], axis=2),
        axis=2,
    )
    coverage = float(np.count_nonzero(classified)) / float(classified.size) * 100.0
    return _round_score(coverage)


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
