import re
import pytest

from faker_ru_pii.ru_education_provider import RuEducationProvider


@pytest.mark.parametrize("method, pattern", [
    ("diploma_series", r"[А-Я]{2}|[А-Я]{3}|\d{6}"),
    ("diploma_number", r"\d{7}"),
    ("diploma_series_number", r"([А-Я]{2}|[А-Я]{3}|\d{6}) \d{7}")
])
def test_education_format(faker, num_samples, method, pattern):
    func = getattr(faker, method)
    for _ in range(num_samples):
        value = func()
        assert re.fullmatch(pattern, value), f"Failed for {method}(): {value}"


def test_education_institution(faker, num_samples):
    school_pattern = re.compile(
        r"^(МБОУ|МАОУ|МОУ|ГБОУ|ЧОУ) "
        r"«(Средняя общеобразовательная школа|Гимназия|Лицей|"
        r"Основная общеобразовательная школа|Общеобразовательная школа) № \d{1,3}»( г\. .+)?$"
    )

    expected_universities = set(RuEducationProvider.UNIVERSITIES)

    found_school = False
    found_university = False

    for _ in range(num_samples):
        value = faker.education_institution()

        if school_pattern.fullmatch(value):
            found_school = True
        elif value in expected_universities:
            found_university = True
        else:
            pytest.fail(f"Unexpected institution format: {value}")

        if found_school and found_university:
            break

    assert found_school
    assert found_university
