import random
from typing import Tuple, Union, Dict, Any

from PIL.Image import Image

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.color.generate_color import generate_hsluv_text_contrasting_color
from lambdawaker.draw.color.utils import get_random_point_with_margin
from lambdawaker.random.values import DefaultValue, Default, Random


def generate_random_voronoid_parameters(
        img: Image,
        primary_color: Union[ColorUnion, Random] = Random,
        right_corner: Union[Tuple[int, int], Default, Random] = Default,
        size: Union[Tuple[int, int], Default, Random] = Default,
        angle_degrees: Union[float, int, Default, Random] = Default
) -> Dict[str, Any]:
    """
    Generates random parameters for a Voronoi (voronoid) gradient.

    Args:
        img (Image): The image for which the parameters are being generated.
        primary_color (Union[ColorUnion, Random], optional): The primary color.
        right_corner (Union[Tuple[int, int], Default, Random], optional): The top-left corner.
        size (Union[Tuple[int, int], Default, Random], optional): The size of the area.

    Returns:
        Dict[str, Any]: A dictionary containing the generated parameters.
    """
    if primary_color == Random:
        primary_color = generate_hsluv_text_contrasting_color()
    else:
        primary_color = to_hsluv_color(primary_color)

    color_a = primary_color.close_color()
    color_b = primary_color.harmonious_noticeable_color()

    if right_corner == Default:
        right_corner = DefaultValue((0, 0))

    if size == Default:
        size = DefaultValue(lambda: img.size)

    if angle_degrees == Random:
        angle_degrees = random.uniform(0, 360)
    if angle_degrees == Default:
        angle_degrees = 45

    return {
        "right_corner": get_random_point_with_margin(img.size, default=right_corner, margin=0),
        "size": get_random_point_with_margin(img.size, default=size, margin=0),
        "color_a": color_a,
        "color_b": color_b,
        "timestamp": random.uniform(0.0, 100.0),
        "scale": random.uniform(5, 25),
        "angle_degrees": angle_degrees
    }
