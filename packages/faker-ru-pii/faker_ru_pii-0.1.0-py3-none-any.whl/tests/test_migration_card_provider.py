import re
import pytest


@pytest.mark.parametrize("method, pattern", [
    ("migration_card_number", r"^[1-9]\d{3}$"),
    ("migration_card_series_number", r"^[1-9]\d{3} [1-9]\d{6}")
])
def test_driver_license_format(faker, num_samples, method, pattern):
    func = getattr(faker, method)
    for _ in range(num_samples):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"
