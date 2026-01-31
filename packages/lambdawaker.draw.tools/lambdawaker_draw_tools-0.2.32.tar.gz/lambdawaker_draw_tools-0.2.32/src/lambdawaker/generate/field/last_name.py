import os

from importlib import resources
from lambdawaker.random.selection.select_random_word_from_nested_directory import select_random_word_from_nested_directory


def generate_last_name():
    db_path = str(resources.files("lambdawaker").joinpath("assets/text/last_name")) + os.sep

    name, source = select_random_word_from_nested_directory(
        db_path
    )

    return {
        "data": name,
        "source": source
    }


def vis():
    print(generate_last_name())


if __name__ == "__main__":
    vis()
