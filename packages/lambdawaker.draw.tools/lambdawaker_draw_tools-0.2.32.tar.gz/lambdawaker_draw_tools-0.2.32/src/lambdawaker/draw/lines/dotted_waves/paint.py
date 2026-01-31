import math
import random
from typing import Tuple, Union, Optional, Any

import aggdraw
from PIL import Image
from noise import pnoise2

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.lines.dotted_waves.parameters import generate_random_dotted_waves_parameters
from lambdawaker.random.values import Random, Default, clean_passed_parameters


def paint_dotted_waves(
        image: Image.Image,
        area_size: Optional[Tuple[int, int]] = None,
        num_lines: int = 200,
        margin: float = 0.2,
        angle: float = 0.0,
        base_width: float = 1.0,
        max_width: float = 4.0,
        width_noise_scale: float = 0.015,
        step: int = 15,
        overlap: float = 1.5,
        amp: float = 25.0,
        scale: float = 0.003,
        noise_x_offset: float = 0.0,
        noise_y_offset: float = 0.0,
        phase: float = 0.0,
        width_noise_x: float = 0.0,
        width_noise_y: float = 0.0,
        mod: float = 100.0,
        wobble_dir: int = 1,
        color: ColorUnion = (120, 140, 160, 255),
) -> None:
    """
    Draw dotted waves into an existing image.
    """
    color_obj = to_hsluv_color(color)
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

    # projection lengths
    travel_len = abs(dx) * W + abs(dy) * H
    dist_len = abs(px) * W + abs(py) * H

    cx = width / 2
    cy = height / 2

    # safety: keep widths sensible
    base_w = float(base_width)
    max_w = float(max_width)
    if max_w < base_w:
        base_w, max_w = max_w, base_w

    steps_count = int(travel_len / step) + 2

    for i in range(num_lines):
        # distribute lines across perpendicular axis
        t = (-dist_len / 2) + dist_len * (i / num_lines) + rng.uniform(-1.0, 1.0)

        # start before the rectangle along the travel axis
        current_x = cx + px * t - dx * (travel_len / 2)
        current_y = cy + py * t - dy * (travel_len / 2)

        prev_x, prev_y = current_x, current_y
        last_variation = 0.0

        for s in range(steps_count):
            # shape noise
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

            # thickness variation (smooth)
            w_noise = pnoise2(
                (s * step + width_noise_x) * width_noise_scale,
                (i * 13.7 + width_noise_y) * width_noise_scale,
                octaves=1,
                persistence=0.5,
                lacunarity=2.0,
            )
            w_t = (w_noise + 1.0) * 0.5  # [-1,1] -> [0,1]
            seg_width_f = base_w + (max_w - base_w) * w_t
            seg_width = max(1, int(round(seg_width_f)))

            # To mimic original color variation based on last_variation:
            v = last_variation * 30
            line_color = color_obj.copy().add_lightness(v)

            pen = aggdraw.Pen(
                line_color.to_rgba(),
                width=seg_width,
                opacity=50,
            )

            # --- GAP FIX: extend segment a little past both ends ---
            vx = current_x - prev_x
            vy = current_y - prev_y
            vlen = math.hypot(vx, vy)

            if vlen > 1e-9:
                ux = vx / vlen
                uy = vy / vlen

                # make overlap scale a bit with thickness (prevents cracks on thick parts)
                o = overlap + 0.35 * seg_width
                x1 = prev_x - ux * o
                y1 = prev_y - uy * o
                x2 = current_x + ux * o
                y2 = current_y + uy * o
            else:
                x1, y1, x2, y2 = prev_x, prev_y, current_x, current_y

            draw.line([x1, y1, x2, y2], pen)

            prev_x, prev_y = current_x, current_y

    draw.flush()


def paint_random_dotted_waves(
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

    parameters = generate_random_dotted_waves_parameters(img, primary_color, color, area_size)

    parameters = parameters | passed_values
    paint_dotted_waves(img, **parameters)
    return parameters
