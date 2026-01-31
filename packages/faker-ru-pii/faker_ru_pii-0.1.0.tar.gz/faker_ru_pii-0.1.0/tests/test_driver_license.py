import re
import pytest


@pytest.mark.parametrize("method, pattern", [
    ("driver_license_number", r"\№?\d{6}"),
    ("driver_license_series", r"\d{2}\s?\d{2}"),
    ("driver_license_full", r"\d{2}\s?\d{2}\s?\№?\d{6}")
])
def test_driver_license_format(faker, num_samples, method, pattern):
    func = getattr(faker, method)
    for _ in range(num_samples):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"
