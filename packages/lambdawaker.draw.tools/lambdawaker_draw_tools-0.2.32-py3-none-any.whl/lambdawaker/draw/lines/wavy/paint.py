import math
import random
from typing import Tuple, Union, Optional, Any

import aggdraw
from PIL import Image
from noise import pnoise2

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.lines.wavy.parameters import generate_random_wavy_parameters
from lambdawaker.random.values import Random, Default, clean_passed_parameters


def paint_wavy(
        image: Image.Image,
        area_size: Optional[Tuple[int, int]] = None,
        num_lines: int = 200,
        margin: float = 0.2,
        angle: float = 0.0,
        step: int = 15,
        amp: float = 25,
        scale: float = 0.003,
        noise_x_offset: float = 0.0,
        noise_y_offset: float = 0.0,
        phase: float = 0.0,
        mod: float = 100.0,
        wobble_dir: int = 1,
        thickness: float = 2,
        color: ColorUnion = (0, 0, 0, 255),
) -> None:
    """
    Draw wavy lines into an existing image.
    """
    color = to_hsluv_color(color)
    rng = random.SystemRandom()

    if area_size is None:
        area_size = image.size

    width, height = area_size
    margin_x = width * margin
    margin_y = height * margin

    draw = aggdraw.Draw(image)

    # --- angle vectors (unit) ---
    theta = math.radians(angle)
    dx = math.cos(theta)
    dy = math.sin(theta)

    # perpendicular unit vector
    px = -dy
    py = dx

    # expanded canvas dimensions (so lines start/end offscreen)
    W = width + 2 * margin_x
    H = height + 2 * margin_y

    # projection lengths of the expanded rectangle onto travel/perp axes
    travel_len = abs(dx) * W + abs(dy) * H
    dist_len = abs(px) * W + abs(py) * H

    cx = width / 2
    cy = height / 2

    for i in range(num_lines):
        # distribute across perpendicular axis
        t = (-dist_len / 2) + dist_len * (i / num_lines) + rng.uniform(-1.0, 1.0)

        # start before the rectangle along the travel axis
        current_x = cx + px * t - dx * (travel_len / 2)
        current_y = cy + py * t - dy * (travel_len / 2)

        coords = [current_x, current_y]
        last_variation = 0.0

        steps_count = int(travel_len / step) + 2  # small buffer

        for _ in range(steps_count):
            last_variation = pnoise2(
                (current_x + noise_x_offset + phase) * scale,
                (current_y + noise_y_offset) * scale,
                octaves=2,
                persistence=0.5,
                lacunarity=2.0,
            )

            # move forward
            current_x += dx * step
            current_y += dy * step

            # wobble sideways (perpendicular to travel)
            wobble = (
                    last_variation
                    * amp
                    * math.sin((current_x + current_y) / mod)
                    * wobble_dir
            )
            current_x += px * wobble
            current_y += py * wobble

            coords.extend([current_x, current_y])

        # We use the color provided, but can apply slight variations based on noise if we want to mimic test7 fully.
        # However, the architecture usually expects the color to be respected.
        # In test7, color_val was based on last_variation.
        # For now, let's keep it simple or allow slight variation of the provided color.

        # To mimic test7's color variation:
        v = last_variation * 60
        # HSLuv variation (adjusting lightness slightly)
        l_variation = v * 0.5  # scale it down a bit
        line_color = color.copy().add_lightness(l_variation)

        pen = aggdraw.Pen(
            line_color.to_rgba(),
            width=thickness,
            opacity=rng.randint(90, 180),
        )

        draw.line(coords, pen)

    draw.flush()


def paint_random_wavy(
        img: Image.Image,
        primary_color: Union[ColorUnion, Random] = Random,
        color: Optional[ColorUnion] = Default,
        area_size: Union[Tuple[int, int], Default, Random] = Default,
        num_lines: Union[int, Default, Random] = Default,
        angle: Union[float, Default, Random] = Default,
) -> dict[str, Any]:
    passed_values = clean_passed_parameters({
        "area_size": area_size,
        "num_lines": num_lines,
        "angle": angle,
        "color": color,
    })

    parameters = generate_random_wavy_parameters(img, primary_color, color, area_size)

    parameters = parameters | passed_values
    paint_wavy(img, **parameters)
    return parameters
