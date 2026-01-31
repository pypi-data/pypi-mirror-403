import re

from string import ascii_uppercase

from faker.providers.passport.ru_RU import Provider as FakerPassportProvider

_SUBJECT_BY_CODE = {
    '77': "г. Москве",
    '78': "г. Санкт-Петербурге",
    '92': "г. Севастополе",
    '90': "г. Москве",
    '50': "Московской области",
    '47': "Ленинградской области",
    '66': "Свердловской области",
    '54': "Новосибирской области",
    '16': "Республике Татарстан",
    '02': "Республике Башкортостан",
    '23': "Краснодарском крае",
    '25': "Приморскому краю",
    '61': "Ростовской области",
    '63': "Самарской области",
    '74': "Челябинской области",
    '36': "Воронежской области",
    '42': "Кемеровской области — Кузбассе",
    '52': "Нижегородской области",
    '55': "Омской области",
    '64': "Саратовской области",
    '72': "Тюменской области",
    '27': "Хабаровскому краю",
    '22': "Алтайскому краю",
    '05': "Республике Дагестан",
    '14': "Республике Саха (Якутия)",
    '24': "Красноярскому краю",
    '07': "Кабардино-Балкарской Республике",
    '26': "Ставропольскому краю",
}

_VALID_SUBJECT_CODES = list(_SUBJECT_BY_CODE.keys())


class PassportProvider(FakerPassportProvider):
    _SUBJECT_BY_CODE = _SUBJECT_BY_CODE
    _VALID_SUBJECT_CODES = _VALID_SUBJECT_CODES

    passport_series_formats = (
        "%###",
    )

    passport_only_number_formats = (
        "######",
    )

    ru_subject_codes = [
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "57",
        "58",
        "59",
        "60",
        "61",
        "62",
        "63",
        "64",
        "65",
        "66",
        "67",
        "68",
        "69",
        "70",
        "71",
        "72",
        "73",
        "74",
        "75",
        "76",
        "77",
        "78",
        "79",
        "83",
        "86",
        "87",
        "89",
        "91",
        "92",
        "94",
        "95"
    ]

    def passport_full(self) -> str:
        dept_code = self.department_code().replace("-", "")
        series_number = self.passport_series()

        number = self.passport_number()
        full_series_number = self.passport_series_number()

        issuing_authority = self.passport_issuing_authority(dept_code)

        templates = [
            "{series_number} выдан {authority}",
            "{series_number}, выдан {authority}",
            "Паспорт {series_number} выдан {authority}",
            "{series_number} выдано {authority}",
            "{series_number} (выдан {authority})",
            "{series_number}. Выдан: {authority}",
            "серия {series} № {number}, выдан {authority}",
            "Серия {series}, номер {number}, выдан {authority}",
        ]

        template = self.generator.random.choice(templates)

        return template.format(
            series_number=full_series_number,
            series=series_number,
            number=number,
            authority=issuing_authority
        )

    def passport_issuing_authority(self, department_code: str | None = None) -> str:

        if department_code is None:
            subject_code = self.generator.random.choice(self._VALID_SUBJECT_CODES)
        else:
            subject_code = department_code[:2]

        subject_name = self._SUBJECT_BY_CODE.get(subject_code, "г. Москве")  # fallback

        prefixes = [
            "Отделение Управления МВД России по",
            "Межрайонное отделение Управления МВД России по",
            "Отдел Управления по вопросам миграции МВД России по",
        ]
        prefix = self.generator.random.choice(prefixes)

        if self.generator.random.random() < 0.35:
            districts = [
                "в Центральному району",
                "в Ленинскому району",
                "в Октябрьскому району",
                "в г. Туле",
                "в г. Казани",
                "в г. Екатеринбурге",
                "в г. Новосибирске",
                "в Калининскому району",
            ]
            district = self.generator.random.choice(districts)
            return f"{prefix} {subject_name} {district}"
        else:
            return f"{prefix} {subject_name}"

    def passport_series_number(self) -> str:
        return super().passport_number()

    def passport_number(self) -> str:
        temp = re.sub(
            r"\?",
            lambda _: self.random_element(ascii_uppercase),
            self.random_element(self.passport_only_number_formats),
        )
        return self.numerify(temp)

    def passport_series(self) -> str:
        temp = re.sub(
            r"\?",
            lambda _: self.random_element(ascii_uppercase),
            self.random_element(self.passport_series_formats),
        )
        return self.numerify(temp)

    def department_code(self) -> str:
        subject_code = self.generator.random.choice(self.ru_subject_codes)
        oragnization_type = self.generator.random.choice(["0", "1", "2", "3"])
        division_code = f"{self.generator.random.randint(1, 999):03d}"
        return f"{subject_code}{oragnization_type}-{division_code}"
