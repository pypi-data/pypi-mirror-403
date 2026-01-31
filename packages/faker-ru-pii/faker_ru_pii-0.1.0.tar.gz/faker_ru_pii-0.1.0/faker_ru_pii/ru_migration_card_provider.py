from faker.providers import BaseProvider


class RuMigrationCardProvider(BaseProvider):
    """
        - [X] Номер миграционной карты
        - [X] Серия + номер миграционной карты
        https://tinyurl.com/45d3fs4d
    """

    def migration_card_series_number(self) -> str:
        return self.numerify("%### %######")

    def migration_card_number(self) -> str:
        return self.numerify("%###")
