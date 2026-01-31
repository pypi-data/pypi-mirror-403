import random
from typing import Union, Tuple


class PseudoTextGenerator:
    def __init__(self):
        self.consonants = "bcdfghjklmnpqrstvwxyz"
        self.vowels = "aeiou"
        self.punctuation = [".", ".", ".", "!", "?"]

    def _generate_syllable(self) -> str:
        """Creates a basic CV (Consonant-Vowel) or CVC syllable."""
        c1 = random.choice(self.consonants)
        v = random.choice(self.vowels)
        # 30% chance of adding a trailing consonant (CVC)
        v2 = random.choice(self.vowels) if random.random() > 0.9 else ""
        c2 = random.choice(self.consonants) if random.random() > 0.9 else ""
        return f"{c1}{v}{v2}{c2}"

    def letter(self):
        return random.choice(self.consonants + self.vowels)

    def word(self, param: Union[int, Tuple[int, int]] = None) -> str:
        """Combines random syllables into a single word."""
        param = param if param is not None else (2, 4)
        items = 1

        if isinstance(param, tuple):
            items = random.randint(*param)
        elif isinstance(param, int) and param > 1:
            items = param

        word = "".join(self._generate_syllable() for _ in range(items))
        return word

    def sentence(self, param: Union[int, Tuple[int, int]] = None, p=True) -> str:
        """Combines random syllables into a single word."""
        param = param if param is not None else (4, 8)
        items = 1

        if isinstance(param, tuple):
            items = random.randint(*param)
        elif isinstance(param, int) and param > 1:
            items = param

        population = [1, 2, 3, 4]
        weights = [0.15, 0.20, 0.60, 0.05]

        # Generate 'n' numbers at once
        words_sizes = random.choices(population, weights=weights, k=items)
        words = [self.word(s) for s in words_sizes]

        # Capitalize first word and add a random ending punctuation
        sentence = " ".join(words).capitalize()

        if not p:
            return sentence

        return f"{sentence}{random.choice(self.punctuation)}"

    def paragraph(self, sentences: int = 5) -> str:
        """Combines sentences into a paragraph."""
        return " ".join(self.sentence() for _ in range(sentences))


if __name__ == "__main__":
    lorem = PseudoTextGenerator()
    print(lorem.word((2, 4)))
