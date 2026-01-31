import re


def test_series_number(passport_provider, num_samples):
    for _ in range(num_samples):
        r = passport_provider.passport_series_number()
        assert re.fullmatch(r"\d{2}\s*\d{2}\s?\d{6}", r)


def test_department_code(passport_provider, num_samples):
    for _ in range(num_samples):
        r = passport_provider.department_code()
        assert re.fullmatch(r"\d{3}-\d{3}", r)


def test_series(passport_provider, num_samples):
    for _ in range(num_samples):
        r = passport_provider.passport_series()
        assert re.fullmatch(r"\d{2}\s*\d{2}", r)


def test_number(passport_provider, num_samples):
    for _ in range(num_samples):
        r = passport_provider.passport_number()
        assert re.fullmatch(r"\d{6}", r)


def test_passport_issuing_authority(passport_provider, num_samples):
    # TODO: fix logic + implement test
    passport_provider.passport_issuing_authority()


def test_passport_full(passport_provider, num_samples):
    # TODO: implement test
    passport_provider.passport_full()
