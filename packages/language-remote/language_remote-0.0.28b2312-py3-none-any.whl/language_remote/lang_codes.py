from .lang_code import LangCode

class LangCodes:
    @staticmethod
    def all_lang_codes():
        return [lang.value for lang in LangCode]

    @staticmethod
    def all_lang_names():
        return [lang.name for lang in LangCode]

    @staticmethod
    def codes_to_names():
        return {lang.value: lang.name for lang in LangCode}

    @staticmethod
    def names_to_codes():
        return {lang.name: lang.value for lang in LangCode}
