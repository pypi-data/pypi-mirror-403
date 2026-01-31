import re
import pytest


@pytest.mark.parametrize("method, pattern", [
    ("foreign_passport_number_new", r"\d{9}"),
    ("foreign_passport_number_old", r"\d{7}"),
    ("foreign_passport_series_old", r"\d{2}"),
    ("foreign_passport_number", r"\d{7}|\d{9}"),
    ("foreign_passport_series", r"\d{0}|\d{2}"),
])
def test_passport_format(foreign_passport_provider, method, pattern):
    func = getattr(foreign_passport_provider, method)
    for _ in range(100):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"


def test_foreign_passport_full(foreign_passport_provider, num_samples):
    for _ in range(num_samples):
        r = foreign_passport_provider.foreign_passport_full()
        assert re.fullmatch(r"(\d{9})|(\d{2}\s?\№?\d{7})", r)
