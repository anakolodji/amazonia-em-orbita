from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping
from urllib.parse import urlencode

import cv2
import numpy as np
import requests


GIBS_WMS_ENDPOINT = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
GIBS_ACKNOWLEDGEMENT = (
    "Imagery provided by NASA Global Imagery Browse Services (GIBS), "
    "part of NASA ESDIS."
)


@dataclass(frozen=True)
class GIBSLayer:
    label: str
    identifier: str
    image_format: str = "image/jpeg"


@dataclass(frozen=True)
class GIBSRegion:
    label: str
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class GIBSScene:
    image_bgr: np.ndarray
    label: str
    source_url: str
    acknowledgement: str = GIBS_ACKNOWLEDGEMENT


GIBS_LAYER_OPTIONS: Mapping[str, GIBSLayer] = {
    "MODIS Terra True Color": GIBSLayer(
        label="MODIS Terra True Color",
        identifier="MODIS_Terra_CorrectedReflectance_TrueColor",
    ),
    "VIIRS SNPP True Color": GIBSLayer(
        label="VIIRS SNPP True Color",
        identifier="VIIRS_SNPP_CorrectedReflectance_TrueColor",
    ),
    "MODIS Terra Bands 7-2-1": GIBSLayer(
        label="MODIS Terra Bands 7-2-1",
        identifier="MODIS_Terra_CorrectedReflectance_Bands721",
    ),
}

GIBS_REGION_OPTIONS: Mapping[str, GIBSRegion] = {
    "Yanomami / Roraima": GIBSRegion(
        label="Yanomami / Roraima",
        bbox=(-66.8, -1.0, -61.2, 5.4),
    ),
    "Alto Rio Negro / Amazonas": GIBSRegion(
        label="Alto Rio Negro / Amazonas",
        bbox=(-68.4, -2.0, -62.4, 2.0),
    ),
    "Amazônia Ocidental": GIBSRegion(
        label="Amazônia Ocidental",
        bbox=(-72.5, -8.5, -58.0, 5.5),
    ),
}


class GIBSImageError(RuntimeError):
    pass


def build_gibs_wms_url(
    *,
    layer: GIBSLayer,
    image_date: date,
    bbox: tuple[float, float, float, float],
    width: int = 960,
    height: int = 640,
) -> str:
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.1.1",
        "LAYERS": layer.identifier,
        "STYLES": "",
        "FORMAT": layer.image_format,
        "TRANSPARENT": "false",
        "SRS": "EPSG:4326",
        "BBOX": ",".join(_format_coord(value) for value in bbox),
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "TIME": image_date.isoformat(),
    }
    return f"{GIBS_WMS_ENDPOINT}?{urlencode(params)}"


def fetch_gibs_scene(
    *,
    layer: GIBSLayer,
    region: GIBSRegion,
    image_date: date,
    width: int = 960,
    height: int = 640,
    http_client=requests,
) -> GIBSScene:
    url = build_gibs_wms_url(
        layer=layer,
        image_date=image_date,
        bbox=region.bbox,
        width=width,
        height=height,
    )
    try:
        response = http_client.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise GIBSImageError(f"Falha ao baixar imagem NASA GIBS: {exc}") from exc

    content_type = getattr(response, "headers", {}).get("content-type", "")
    if content_type and not content_type.startswith("image/"):
        raise GIBSImageError(f"NASA GIBS retornou conteúdo inesperado: {content_type}")

    buffer = np.frombuffer(response.content, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise GIBSImageError("NASA GIBS retornou uma imagem vazia ou inválida.")

    return GIBSScene(
        image_bgr=image,
        label=f"{layer.label} - {region.label} - {image_date.isoformat()}",
        source_url=url,
    )


def _format_coord(value: float) -> str:
    return f"{float(value):.6f}".rstrip("0").rstrip(".")
