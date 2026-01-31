import re
import pytest


@pytest.mark.parametrize("method, pattern", [
    ("birth_certificate_number", r"\d{6}"),
    ("birth_certificate_series", r"(I|II|III|IV|V|VI|VII|VIII|IX|X)-[А-Я]{2}"),
    ("birth_certificate_full", r"(I|II|III|IV|V|VI|VII|VIII|IX|X)\s?\-?[А-Я]{2} \d{6}")
])
def test_birth_certificate_format(faker, num_samples, method, pattern):
    func = getattr(faker, method)
    for _ in range(num_samples):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"
