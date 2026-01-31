from PIL import Image

from lambdawaker.draw.color.HSLuvColor import ColorUnion
from lambdawaker.draw.gradient.voronoid.paint import paint_voronoid, paint_random_voronoid


def create_voronoid(
        width: int = 1920,
        height: int = 1080,
        color_a: ColorUnion = (193, 41, 46, 255),
        color_b: ColorUnion = (241, 211, 2, 255),
        timestamp: float = 1.0,
        scale: float = 30.0,
) -> Image.Image:
    """
    Create an RGBA image and draw a Voronoi (voronoid) gradient on it.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    paint_voronoid(
        image=img,
        right_corner=(0, 0),
        size=(width, height),
        color_a=color_a,
        color_b=color_b,
        timestamp=timestamp,
        scale=scale,
    )

    return img


def create_random_voronoid(
        width: int = 1920,
        height: int = 1080,
) -> Image.Image:
    """
    Create an RGBA image and draw a random Voronoi (voronoid) gradient on it.
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    paint_random_voronoid(img, right_corner=(0, 0), size=(width, height))
    return img


def vis():
    img = create_random_voronoid(width=1280, height=720)
    img.show()


if __name__ == '__main__':
    vis()
