from faker.providers import BaseProvider


class RuForeignPassportProvider(BaseProvider):

    def foreign_passport_full(self) -> str:
        if self.generator.random.choice([True, False]):
            series = self.foreign_passport_series_old()
            number = self.foreign_passport_number_old()
            return self.generator.random.choice([f"{series} {number}", f"{series}№{number}"])
        else:
            return self.foreign_passport_number_new()

    def foreign_passport_series(self) -> str:
        if self.generator.random.choice([True, False]):
            return self.foreign_passport_series_old()
        else:
            return self.foreign_passport_number_new()[:2]

    def foreign_passport_number(self) -> str:
        if self.generator.random.choice([True, False]):
            return self.foreign_passport_number_old()
        else:
            return self.foreign_passport_number_new()

    def foreign_passport_series_old(self) -> str:
        return f"{self.generator.random.randint(10, 99):02d}"

    def foreign_passport_number_old(self) -> str:
        return f"{self.generator.random.randint(1_000_000, 9_999_999):07d}"

    def foreign_passport_number_new(self) -> str:
        return f"{self.generator.random.randint(100_000_000, 999_999_999):09d}"
