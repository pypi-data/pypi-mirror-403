from faker.providers import BaseProvider


class RuResidencePermitProvider(BaseProvider):

    serials = [
        "82",
        "83",
        "80",
        "81",
        "90"
    ]

    def residence_permit_full(self) -> str:
        number = self.residence_permit_number()
        serial = self.residence_permit_serial()

        separator = self.generator.random.choice(["№", "", " "])

        return serial + separator + number

    def residence_permit_number(self) -> str:
        return str(self.random_number(digits=7, fix_len=True))

    def residence_permit_serial(self) -> str:
        return self.generator.random.choice(self.serials)
