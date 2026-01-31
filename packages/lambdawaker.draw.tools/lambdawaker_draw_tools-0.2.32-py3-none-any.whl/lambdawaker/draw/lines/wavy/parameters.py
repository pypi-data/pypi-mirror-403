import random
from typing import Tuple, Union, Dict, Any

from PIL import Image

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.color.generate_color import generate_hsluv_black_text_contrasting_color
from lambdawaker.draw.color.utils import get_random_point_with_margin
from lambdawaker.random.values import DefaultValue, Default, Random


def generate_random_wavy_parameters(
        img: Image.Image,
        primary_color: Union[ColorUnion, Random] = Random,
        color: Union[ColorUnion, Default, Random] = Default,
        size: Union[Tuple[int, int], Default, Random] = Default
) -> Dict[str, Any]:
    """
    Generates random parameters for wavy lines.

    Args:
        img (Image.Image): The image for which the parameters are being generated.
        primary_color (Union[ColorUnion, Random], optional): The primary color used to derive other colors if they are not specified.
            If `Random`, a random contrasting color is generated. Defaults to `Random`.
        color (Union[ColorUnion, Default, Random], optional): The color of the lines.
            If `Default`, a color derived from `primary_color` is used.
            If `Random`, a random contrasting color is generated.
            Defaults to `Default`.
        size (Union[Tuple[int, int], Default, Random], optional): The size of the area.
            If Default, it defaults to the image size. If Random, a random point with no margin is chosen.
            Defaults to Default.

    Returns:
        Dict[str, Any]: A dictionary containing the generated parameters.
    """
    if primary_color == Random:
        primary_color = generate_hsluv_black_text_contrasting_color()
    else:
        primary_color = to_hsluv_color(primary_color)

    if color == Default:
        color = primary_color.close_color()
    elif color == Random:
        color = generate_hsluv_black_text_contrasting_color()

    if size == Default:
        size = DefaultValue(lambda: img.size)

    rng = random.SystemRandom()

    return {
        "area_size": get_random_point_with_margin(img.size, default=size, margin=0),
        "num_lines": random.randint(150, 250),
        "margin": 0.2,
        "angle": random.uniform(0, 360),
        "step": 15,
        "amp": rng.randint(25, 30),
        "scale": 0.003,
        "noise_x_offset": rng.uniform(-200, 200),
        "noise_y_offset": rng.uniform(-200, 200),
        "phase": rng.uniform(0, 100),
        "mod": rng.uniform(50, 500),
        "wobble_dir": rng.choice((-1, 1)),
        "thickness": 2,
        "color": color,
    }
