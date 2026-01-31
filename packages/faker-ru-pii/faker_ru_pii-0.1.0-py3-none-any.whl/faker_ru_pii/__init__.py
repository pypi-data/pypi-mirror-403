from faker import Faker as BaseFaker
from faker_ru_pii.ru_passport_provider import PassportProvider
from faker_ru_pii.ru_residence_permit_provider import RuResidencePermitProvider
from faker_ru_pii.ru_foreign_passport_provider import RuForeignPassportProvider
from faker_ru_pii.ru_birth_certificate_provider import RuBirthCertificateProvider
from faker_ru_pii.ru_driver_license import RuDriverLicenseProvider
from faker_ru_pii.ru_military_id_provider import RuMilitaryIdProvider
from faker_ru_pii.ru_education_provider import RuEducationProvider
from faker_ru_pii.ru_migration_card_provider import RuMigrationCardProvider


providers = [
    PassportProvider,
    RuResidencePermitProvider,
    RuForeignPassportProvider,
    RuBirthCertificateProvider,
    RuDriverLicenseProvider,
    RuMilitaryIdProvider,
    RuEducationProvider,
    RuMigrationCardProvider
]

__all__ = providers


class Faker(BaseFaker):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        for provider in providers:
            self.add_provider(provider)
