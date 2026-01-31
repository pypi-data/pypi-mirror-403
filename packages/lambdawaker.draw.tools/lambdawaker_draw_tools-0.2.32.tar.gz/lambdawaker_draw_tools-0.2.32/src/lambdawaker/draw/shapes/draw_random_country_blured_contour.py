from importlib import resources
from PIL import Image

from lambdawaker.draw.color.HSLuvColor import HSLuvColor, random_alpha
from lambdawaker.draw.shapes.draw_blured_image_contour import draw_contour
from lambdawaker.draw.svg.svg_to_png import svg_to_png
from lambdawaker.random.selection.select_random_file import select_random_file


def draw_random_country_blured_contour(img: Image.Image, primary_color: HSLuvColor):
    source = str(resources.files("lambdawaker").joinpath("assets/img/country_shapes"))
    svg_path = select_random_file(source)

    width, height = img.size
    size = (int(width / 3.2), height)

    country = svg_to_png(svg_path, size)

    color = primary_color.close_color() - random_alpha(.3, .6)
    stroke_color = primary_color.close_color() - random_alpha(.3, .6)

    silhouette = draw_contour(
        country,
        color,
        stroke_color
    )

    _, silhouette_height = silhouette.size

    x = int(width - width / 2.5)
    y = int(height // 2 - silhouette_height // 2)

    img.paste(silhouette, (x, y), silhouette)

    return {
        "color": color,
        "stroke_color": stroke_color
    }
