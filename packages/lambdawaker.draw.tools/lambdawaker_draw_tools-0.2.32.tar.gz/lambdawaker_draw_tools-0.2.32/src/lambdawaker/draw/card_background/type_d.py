from typing import Union

from PIL import Image

from lambdawaker.draw import gradient as fill_module
from lambdawaker.draw import grid as grid_module
from lambdawaker.draw import lines as waves_module
from lambdawaker.draw.color.HSLuvColor import random_alpha, ColorUnion
from lambdawaker.draw.color.generate_color import generate_hsluv_black_text_contrasting_color
from lambdawaker.draw.shapes.draw_random_country_blured_contour import draw_random_country_blured_contour
from lambdawaker.log.Profiler import Profiler
from lambdawaker.random.values import Random
from lambdawaker.reflection.query import select_random_function_from_module_and_submodules


def generate_card_background_type_d(size=(800, 600), primary_color: Union[ColorUnion | Random] = Random):
    if primary_color == Random:
        primary_color = generate_hsluv_black_text_contrasting_color()

    width, height = size
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    profiler = Profiler(False)

    profiler.start("SELECTING FUNCTIONS")
    background_paint_function = select_random_function_from_module_and_submodules(fill_module, "paint_random_.*")
    background_details = select_random_function_from_module_and_submodules(grid_module, "paint_random_.*")
    lines_details = select_random_function_from_module_and_submodules(waves_module, "paint_random_.*")
    selecting_functions_time = profiler.finalize("SELECTING FUNCTIONS")

    draw_functions = [
        background_paint_function,
        background_details,
        draw_random_country_blured_contour,
        lines_details,
    ]

    colors = [
        primary_color,
        primary_color.close_color() - random_alpha(.6, .8),
        primary_color.close_color() - random_alpha(.1, .3),
        primary_color.close_color() - random_alpha(.6, .8),
    ]

    operations = []

    profiler.start("DRAWING")

    for i, func in enumerate(draw_functions):
        profiler.start(f"DRAWING {func.__name__}")
        color = colors[i]

        parameters = func(
            img,
            primary_color=color,
        )

        elapsed = profiler.finalize(f"DRAWING {func.__name__}")

        operations.append({
            "parameters": parameters,
            "function": func.__name__,
            "color": color,
            "elapsed": elapsed
        })

    drawing_time = profiler.finalize("DRAWING")

    log = {
        "operations": operations,
        "type": "type_a",
        "primary_color": primary_color,
        "selecting_functions_time": selecting_functions_time,
        "drawing_time": drawing_time
    }

    return log, img


def vis():
    log, card = generate_card_background_type_d()
    card.show()


if __name__ == "__main__":
    vis()
