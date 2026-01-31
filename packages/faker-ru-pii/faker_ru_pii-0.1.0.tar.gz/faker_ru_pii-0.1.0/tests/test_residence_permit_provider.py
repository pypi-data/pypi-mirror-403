import re


def test_residence_permit_number(residence_permit_provider, num_samples):
    for _ in range(num_samples):
        r = residence_permit_provider.residence_permit_number()
        assert re.fullmatch(r"\d{7}", r)


def test_residence_permit_serial(residence_permit_provider, num_samples):
    for _ in range(num_samples):
        r = residence_permit_provider.residence_permit_serial()
        assert r in ("82", "83", "80", "81", "90")


def test_residence_permit_full(residence_permit_provider, num_samples):
    for _ in range(num_samples):
        r = residence_permit_provider.residence_permit_full()
        assert re.fullmatch(r"(82|83|80|81|90)\s?\№?\d{7}", r)
