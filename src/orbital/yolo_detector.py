from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np

from orbital.image_analysis import OrbitalImageAnalysis


@dataclass(frozen=True)
class OrbitalDetection:
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]
    model: str

    def as_dict(self) -> dict[str, object]:
        x, y, width, height = self.bbox
        return {
            "Classe": self.label,
            "Confiança": self.confidence,
            "x": x,
            "y": y,
            "largura": width,
            "altura": height,
            "Modelo": self.model,
        }


def detect_orbital_objects(
    analysis: OrbitalImageAnalysis,
    *,
    min_area_ratio: float = 0.015,
) -> list[OrbitalDetection]:
    masks = {
        "água superficial": _mask_for_color(analysis.mask_image_rgb, (30, 104, 210)),
        "vegetação densa": _mask_for_color(analysis.mask_image_rgb, (46, 125, 50)),
        "solo exposto": _mask_for_color(analysis.mask_image_rgb, (191, 126, 41)),
    }
    detections: list[OrbitalDetection] = []
    image_area = analysis.mask_image_rgb.shape[0] * analysis.mask_image_rgb.shape[1]
    min_area = max(1, int(image_area * min_area_ratio))

    for label, mask in masks.items():
        detections.extend(_detections_from_mask(label, mask, min_area, image_area))

    return sorted(detections, key=lambda item: item.confidence, reverse=True)


def detections_to_records(detections: Iterable[OrbitalDetection]) -> list[dict[str, object]]:
    return [detection.as_dict() for detection in detections]


def _mask_for_color(mask_rgb: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    target = np.array(color, dtype=np.uint8)
    return np.where(np.all(mask_rgb == target, axis=2), 255, 0).astype(np.uint8)


def _detections_from_mask(
    label: str,
    mask: np.ndarray,
    min_area: int,
    image_area: int,
) -> list[OrbitalDetection]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections: list[OrbitalDetection] = []
    for contour in contours:
        area = int(cv2.contourArea(contour))
        if area < min_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        confidence = round(min(0.98, 0.55 + (area / image_area) * 2.2), 2)
        detections.append(
            OrbitalDetection(
                label=label,
                confidence=confidence,
                bbox=(int(x), int(y), int(width), int(height)),
                model="YOLO-ready fallback por contornos OpenCV",
            )
        )
    return detections
