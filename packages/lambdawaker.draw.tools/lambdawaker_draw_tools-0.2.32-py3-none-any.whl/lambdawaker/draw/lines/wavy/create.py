from PIL import Image

from lambdawaker.draw.color.HSLuvColor import ColorUnion, to_hsluv_color
from lambdawaker.draw.lines.wavy.paint import paint_wavy, paint_random_wavy


def create_wavy(
        width: int = 800,
        height: int = 600,
        num_lines: int = 200,
        margin: float = 0.2,
        angle: float = 0.0,
        color: ColorUnion = (120, 140, 160, 255),
        bg_color: ColorUnion = (255, 255, 255, 255),
) -> Image.Image:
    """
    Create an RGBA image and draw wavy lines on it.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.
        num_lines (int): Number of lines to draw.
        margin (float): Percentage of width/height for expanded canvas.
        angle (float): Line orientation in degrees.
        color (ColorUnion): Stroke color.
        bg_color (ColorUnion): Background color for the created image.

    Returns:
        PIL.Image.Image: The generated image containing the wavy lines.
    """
    color = to_hsluv_color(color)
    bg_color = to_hsluv_color(bg_color)

    img = Image.new("RGBA", (width, height), bg_color.to_rgba())

    paint_wavy(
        image=img,
        area_size=(width, height),
        num_lines=num_lines,
        margin=margin,
        angle=angle,
        color=color,
    )
    return img


def create_random_wavy(
        width: int = 800,
        height: int = 600,
) -> Image.Image:
    """
    Create an RGBA image and draw random wavy lines on it.

    Args:
        width (int): Width of the output image in pixels.
        height (int): Height of the output image in pixels.

    Returns:
        PIL.Image.Image: The generated image containing the random wavy lines.
    """
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    paint_random_wavy(img, area_size=(width, height))
    return img


def vis():
    img = create_random_wavy()
    img.show()


if __name__ == '__main__':
    vis()
