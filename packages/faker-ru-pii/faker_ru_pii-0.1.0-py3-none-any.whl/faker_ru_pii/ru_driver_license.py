import re

from string import ascii_uppercase
from faker.providers import BaseProvider


class RuDriverLicenseProvider(BaseProvider):

    number_driver_license_format = (
        "######",
        "№######"
    )

    series_driver_license_format = (
        "####",
        "## ##"
    )

    def driver_license_full(self) -> str:
        formats = ["{}{}", "{} {}"]
        series = self.driver_license_series()
        number = self.driver_license_number()
        return self.generator.random.choice(formats).format(series, number)

    def driver_license_series(self) -> str:
        temp = re.sub(
            r"\?",
            lambda _: self.random_element(ascii_uppercase),
            self.random_element(self.series_driver_license_format),
        )
        return self.numerify(temp)

    def driver_license_number(self) -> str:
        temp = re.sub(
            r"\?",
            lambda _: self.random_element(ascii_uppercase),
            self.random_element(self.number_driver_license_format),
        )
        return self.numerify(temp)
