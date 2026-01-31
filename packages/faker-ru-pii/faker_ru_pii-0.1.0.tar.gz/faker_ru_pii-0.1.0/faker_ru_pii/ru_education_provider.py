# https://tinyurl.com/57vx78k9
from faker.providers import BaseProvider


class RuEducationProvider(BaseProvider):

    CYRILLIC_LETTERS = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ"

    diploma_series_format = (
        "%#####",
        "???",
        "??"
    )

    diploma_number_format = (
        "%######",
    )

    UNIVERSITIES = [
        "Московский государственный университет имени М.В. Ломоносова",
        "Санкт-Петербургский государственный университет",
        "Новосибирский государственный университет",
        "Казанский федеральный университет",
        "Уральский федеральный университет имени первого Президента России Б.Н. Ельцина",
        "Московский физико-технический институт (национальный исследовательский университет)",
        "Национальный исследовательский ядерный университет «МИФИ»",
        "Санкт-Петербургский политехнический университет Петра Великого",
        "Высшая школа экономики",
        "Бауманский Московский государственный технический университет",
    ]

    SCHOOL_TYPES = [
        "МБОУ",
        "МАОУ",
        "МОУ"
    ]

    SCHOOL_KINDS = [
        "средняя общеобразовательная школа",
        "гимназия",
        "лицей",
        "основная общеобразовательная школа",
        "общеобразовательная школа"
    ]

    CITIES = [
        "Москвы",
        "Санкт-Петербурга",
        "Казани",
        "Новосибирска",
        "Екатеринбурга",
        "Самары",
        "Ростова-на-Дону"
    ]

    def education_institution(self) -> str:
        if self.generator.boolean():
            school_type = self.generator.random_element(self.SCHOOL_TYPES)
            school_kind = self.generator.random_element(self.SCHOOL_KINDS)
            school_number = self.generator.random_int(1, 999)

            if self.generator.boolean(chance_of_getting_true=30):
                city = self.generator.random_element(self.CITIES)
                return f"{school_type} «{school_kind.capitalize()} № {school_number}» г. {city}"
            else:
                return f"{school_type} «{school_kind.capitalize()} № {school_number}»"
        else:
            return self.generator.random_element(self.UNIVERSITIES)

    def diploma_series_number(self) -> str:
        series = self.diploma_series()
        number = self.diploma_number()
        return f"{series} {number}"

    def diploma_number(self) -> str:
        elem = self.random_element(self.diploma_number_format)
        return self.numerify(elem)

    def diploma_series(self) -> str:
        elem = self.random_element(self.diploma_series_format)
        return self.lexify(elem, self.CYRILLIC_LETTERS) if elem.startswith("?") else self.numerify(elem)
