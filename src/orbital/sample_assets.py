from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_IMAGE_PATH = PROJECT_ROOT / "data" / "sample_images" / "cena_surucucu_orbital.png"


def generate_sample_image(output_path: str | Path = SAMPLE_IMAGE_PATH) -> Path:
    random.seed(42)
    width, height = 960, 640
    image = Image.new("RGB", (width, height), (39, 104, 60))
    draw = ImageDraw.Draw(image, "RGBA")

    for _ in range(2600):
        x = random.randrange(width)
        y = random.randrange(height)
        color = random.choice(
            [
                (29, 92, 48, 90),
                (56, 131, 67, 75),
                (85, 143, 67, 60),
                (21, 78, 47, 85),
            ]
        )
        radius = random.randint(2, 8)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    river_path = [
        (-60, 155),
        (110, 190),
        (265, 250),
        (430, 245),
        (610, 318),
        (770, 355),
        (1030, 410),
    ]
    draw.line(river_path, fill=(26, 89, 159, 235), width=76, joint="curve")
    draw.line(river_path, fill=(42, 128, 191, 210), width=42, joint="curve")

    flood_patches = [
        (180, 295, 345, 400),
        (545, 365, 710, 472),
        (690, 430, 850, 545),
    ]
    for patch in flood_patches:
        draw.ellipse(patch, fill=(42, 123, 185, 150))

    soil_polygons = [
        [(665, 135), (750, 120), (810, 190), (790, 272), (690, 260), (635, 205)],
        [(95, 420), (190, 390), (255, 460), (215, 545), (95, 535), (60, 470)],
        [(430, 92), (505, 76), (560, 126), (548, 194), (458, 205), (408, 150)],
    ]
    for polygon in soil_polygons:
        draw.polygon(polygon, fill=(169, 113, 48, 210))
        draw.line(polygon + [polygon[0]], fill=(112, 82, 42, 150), width=4)

    cloud_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cloud_draw = ImageDraw.Draw(cloud_layer, "RGBA")
    for _ in range(18):
        x = random.randrange(20, width - 120)
        y = random.randrange(20, height - 80)
        cloud_draw.ellipse((x, y, x + 150, y + 44), fill=(245, 247, 235, 34))
    image = Image.alpha_composite(image.convert("RGBA"), cloud_layer.filter(ImageFilter.GaussianBlur(10))).convert("RGB")
    image = image.filter(ImageFilter.GaussianBlur(0.45))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


if __name__ == "__main__":
    print(generate_sample_image())
