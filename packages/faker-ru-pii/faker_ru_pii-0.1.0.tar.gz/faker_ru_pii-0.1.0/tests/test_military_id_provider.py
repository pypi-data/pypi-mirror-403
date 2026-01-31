import re
import pytest


@pytest.mark.parametrize("method, pattern", [
    ("military_id_number", r"\№?\d{7}"),
    ("military_id_series", r"[А-Я]{2}"),
    ("military_id_full", r"[А-Я]{2} \№?\d{7}")
])
def test_driver_license_format(faker, num_samples, method, pattern):
    func = getattr(faker, method)
    for _ in range(num_samples):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"
