from faker.providers import BaseProvider


class RuBirthCertificateProvider(BaseProvider):

    # Кириллические буквы, исключая Ё, Й, Ъ, Ы, Ь
    CYRILLIC_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ"

    ROMAN_NUMERALS = [
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X"
    ]

    def birth_certificate_full(self) -> str:
        series = self.birth_certificate_series()
        number = self.birth_certificate_number()
        series = self.generator.random.choice([series.replace("-", ""), series])
        return " ".join([series, number])

    def birth_certificate_series(self) -> str:
        roman = self.generator.random.choice(self.ROMAN_NUMERALS)
        letters = "".join(
            self.generator.random.choices(self.CYRILLIC_LETTERS, k=2)
        )
        return f"{roman}-{letters}"

    def birth_certificate_number(self) -> str:
        return f"{self.generator.random_int(100_000, 999_999):06d}"
