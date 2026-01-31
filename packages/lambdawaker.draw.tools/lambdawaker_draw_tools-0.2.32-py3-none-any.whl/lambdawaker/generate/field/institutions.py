import os

from importlib import resources
from lambdawaker.random.selection.select_random_word_from_nested_directory import select_random_word_from_nested_directory


def generate_voting_institution_name():
    db_path = str(resources.files("lambdawaker").joinpath("assets/text/institutions")) + os.sep

    name, name_source = select_random_word_from_nested_directory(db_path)

    return {
        "data": name,
        "source": name_source
    }


def vis():
    print(generate_voting_institution_name())


if __name__ == "__main__":
    vis()
