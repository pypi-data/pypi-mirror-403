import pytest
from faker import Faker, Generator
from faker_ru_pii import (
    PassportProvider,
    RuResidencePermitProvider,
    RuForeignPassportProvider,
    RuBirthCertificateProvider,
    RuDriverLicenseProvider,
    RuMilitaryIdProvider,
    RuEducationProvider,
    RuMigrationCardProvider
)


@pytest.fixture
def passport_provider() -> PassportProvider:
    return PassportProvider(generator=Generator())


@pytest.fixture
def residence_permit_provider() -> RuResidencePermitProvider:
    return RuResidencePermitProvider(generator=Generator())


@pytest.fixture
def foreign_passport_provider() -> RuForeignPassportProvider:
    return RuForeignPassportProvider(generator=Generator())


PROVIDERS = [
    RuBirthCertificateProvider,
    RuDriverLicenseProvider,
    RuMilitaryIdProvider,
    RuEducationProvider,
    RuMigrationCardProvider
]


@pytest.fixture
def faker():
    faker = Faker()
    for provider in PROVIDERS:
        faker.add_provider(provider)
    return faker


@pytest.fixture(autouse=True)
def num_samples(request):
    try:
        num = int(request.cls.num_samples)
    except AttributeError:
        num = 100
    return num
