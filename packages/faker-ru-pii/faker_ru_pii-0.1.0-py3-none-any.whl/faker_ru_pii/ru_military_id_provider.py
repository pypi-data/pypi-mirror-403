import re
from string import ascii_uppercase

from faker.providers import BaseProvider


class RuMilitaryIdProvider(BaseProvider):
    """
    Format:
        - Series: 2 Cyrillic letters
        - Number: 7 digits + (random) №
        - Full: "АБ 1234567"
    """

    MILITARY_SERIES_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ"

    number_formats = (
        "#######",
        "№#######"
    )

    def military_id_full(self) -> str:
        return f"{self.military_id_series()} {self.military_id_number()}"

    def military_id_series(self) -> str:
        return self.lexify(text="??", letters=self.MILITARY_SERIES_LETTERS)

    def military_id_number(self) -> str:
        temp = re.sub(
            r"\?",
            lambda _: self.random_element(ascii_uppercase),
            self.random_element(self.number_formats),
        )
        return self.numerify(temp)
