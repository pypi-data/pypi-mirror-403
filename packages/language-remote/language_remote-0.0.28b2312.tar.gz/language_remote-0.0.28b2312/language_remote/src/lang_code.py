from enum import Enum
from langdetect import detect, LangDetectException
from collections import Counter
# We can't use Logger because of circular dependency
# LangCode <- Logger <- UserContext <- LangCode
# use "pytest -s --log-cli-level=INFO" to see logs with pytest
from python_sdk_remote.mini_logger import MiniLogger

# TODO We should split between LangCodes which is all lang codes and LangCode which is the Type/Class
# of one lang code
# TODO We need those values in array or other data structure so we can present all lang code in menu,
# so we can link them to country_id, so we can sort by langauge, sort by country ...

class LangCode(Enum):

    AFRIKAANS = 'af'
    AFRIKAANS_SOUTH_AFRICA = 'af-ZA'
    ARABIC = 'ar'
    ARABIC_UAE = 'ar-AE'
    ARABIC_BAHRAIN = 'ar-BH'
    ARABIC_ALGERIA = 'ar-DZ'
    ARABIC_EGYPT = 'ar-EG'
    ARABIC_IRAQ = 'ar-IQ'
    ARABIC_JORDAN = 'ar-JO'
    ARABIC_KUWAIT = 'ar-KW'
    ARABIC_LEBANON = 'ar-LB'
    ARABIC_LIBYA = 'ar-LY'
    ARABIC_MOROCCO = 'ar-MA'
    ARABIC_OMAN = 'ar-OM'
    ARABIC_QATAR = 'ar-QA'
    ARABIC_SAUDI_ARABIA = 'ar-SA'
    ARABIC_SYRIA = 'ar-SY'
    ARABIC_TUNISIA = 'ar-TN'
    ARABIC_YEMEN = 'ar-YE'
    AZERI = 'az'
    AZERI_LATIN_AZERBAIJAN = 'az-AZ'
    AZERI_CYRILLIC_AZERBAIJAN = 'az-AZ'
    BELARUSIAN = 'be'
    BELARUSIAN_BELARUS = 'be-BY'
    BULGARIAN = 'bg'
    BULGARIAN_BULGARIA = 'bg-BG'
    BOSNIAN = 'bs'
    BOSNIAN_BOSNIA_HERZEGOVINA = 'bs-BA'
    CATALAN = 'ca'
    CATALAN_SPAIN = 'ca-ES'
    CZECH = 'cs'
    CZECH_CZECH_REPUBLIC = 'cs-CZ'
    WELSH = 'cy'
    WELSH_UNITED_KINGDOM = 'cy-GB'
    DANISH = 'da'
    DANISH_DENMARK = 'da-DK'
    GERMAN = 'de'
    GERMAN_AUSTRIA = 'de-AT'
    GERMAN_SWITZERLAND = 'de-CH'
    GERMAN_GERMANY = 'de-DE'
    GERMAN_LIECHTENSTEIN = 'de-LI'
    GERMAN_LUXEMBOURG = 'de-LU'
    DIVEHI = 'dv'
    DIVEHI_MALDIVES = 'dv-MV'
    GREEK = 'el'
    GREEK_GREECE = 'el-GR'
    ENGLISH = 'en'
    ENGLISH_UNITED_KINGDOM = 'en-GB'
    ENGLISH_UNITED_STATES = 'en-US'
    ENGLISH_AUSTRALIA = 'en-AU'
    ENGLISH_BELIZE = 'en-BZ'
    ENGLSIH_CANADA = 'en-CA'
    ENGLISH_CARIBBEAN = 'en-CB'
    ENGLISH_IRELAND = 'en-IE'
    ENGLISH_JAMAICA = 'en-JM'
    ENGLISH_NEW_ZEALAND = 'en-NZ'
    ENGLISH_PHILIPPINES = 'en-PH'
    ENGLISH_SOUTH_AFRICA = 'en-ZA'
    ENGLISH_TRINIDAD = 'en-TT'
    ENGLISH_ZIMBABWE = 'en-ZW'
    ESPERANTO = 'eo'
    SPANISH = 'es'
    SPANISH_ARGENTINA = 'es-AR'
    SPANISH_BOLIVIA = 'es-BO'
    SPANISH_CHILE = 'es-CL'
    SPANISH_COLOMBIA = 'es-CO'
    SPANISH_COSTA_RICA = 'es-CR'
    SPANISH_DOMINICAN_REPUBLIC = 'es-DO'
    SPANISH_ECUADOR = 'es-EC'
    SPANISH_SPAIN = 'es-ES'
    SPANISH_GUATEMALA = 'es-GT'
    SPANISH_HONDURAS = 'es-HN'
    SPANISH_MEXICO = 'es-MX'
    SPANISH_NICARAGUA = 'es-NI'
    SPANISH_PANAMA = 'es-PA'
    SPANISH_PERU = 'es-PE'
    SPANISH_PUERTO_RICO = 'es-PR'
    SPANISH_PARAGUAY = 'es-PY'
    SPANISH_EL_SALVADOR = 'es-SV'
    SPANISH_UNITED_STATES = 'es-US'
    SPANISH_URUGUAY = 'es-UY'
    SPANISH_VENEZUELA = 'es-VE'
    ESTONIAN = 'et'
    ESTONIAN_ESTONIA = 'et-EE'
    BASQUE = 'eu'
    BASQUE_SPAIN = 'eu-ES'
    FARSI = 'fa'
    FARSI_IRAN = 'fa-IR'
    FINNISH = 'fi'
    FINNISH_FINLAND = 'fi-FI'
    FAROESE = 'fo'
    FAROESE_FAROE_ISLANDS = 'fo-FO'
    FRENCH = 'fr'
    FRENCH_BELGIUM = 'fr-BE'
    FRENCH_CANADA = 'fr-CA'
    FRENCH_FRANCE = 'fr-FR'
    FRENCH_LUXEMBOURG = 'fr-LU'
    FRENCH_MONACO = 'fr-MC'
    FRENCH_SWITZERLAND = 'fr-CH'
    GALICIAN = 'gl'
    GALICIAN_SPAIN = 'gl-ES'
    GUJARATI = 'gu'
    GUJARATI_INDIA = 'gu-IN'
    HEBREW = 'he'
    HEBREW_ISRAEL = 'he-IL'
    HINDI = 'hi'
    HINDI_INDIA = 'hi-IN'
    CROATIAN = 'hr'
    CROATIAN_BOSNIA_HERZEGOVINA = 'hr-BA'
    CROATIAN_CROATIA = 'hr-HR'
    HUNGARIAN = 'hu'
    HUNGARIAN_HUNGARY = 'hu-HU'
    ARMENIAN = 'hy'
    ARMENIAN_ARMENIA = 'hy-AM'
    INDONESIAN = 'id'
    INDONESIAN_INDONESIA = 'id-ID'
    ICELANDIC = 'is'
    ICELANDIC_ICELAND = 'is-IS'
    ITALIAN = 'it'
    ITALIAN_SWITZERLAND = 'it-CH'
    ITALIAN_ITALY = 'it-IT'
    JAPANESE = 'ja'
    JAPANESE_JAPAN = 'ja-JP'
    GEORGIAN = 'ka'
    GEORGIAN_GEORGIA = 'ka-GE'
    KAZAKH = 'kk'
    KAZAKH_KAZAKHSTAN = 'kk-KZ'
    KANNADA = 'kn'
    KANNADA_INDIA = 'kn-IN'
    KOREAN = 'ko'
    KOREAN_KOREA = 'ko-KR'
    KONKANI = 'kok'
    KONKANI_INDIA = 'kok-IN'
    KYRGYZ = 'ky'
    KYRGYZ_KYRGYZSTAN = 'ky-KG'
    LITHUANIAN = 'lt'
    LITHUANIAN_LITHUANIA = 'lt-LT'
    LATVIAN = 'lv'
    LATVIAN_LATVIA = 'lv-LV'
    MAORI = 'mi'
    MAORI_NEW_ZEALAND = 'mi-NZ'
    FYRO_MACEDONIAN = 'mk'
    FYRO_MACEDONIAN_FORMER_YUGOSLAV_REPUBLIC_OF_MACEDONIA = 'mk-MK'
    MONGOLIAN = 'mn'
    MONGOLIAN_MONGOLIA = 'mn-MN'
    MARATHI = 'mr'
    MARATHI_INDIA = 'mr-IN'
    MALAY = 'ms'
    MALAY_BRUNEI_DARUSSALAM = 'ms-BN'
    MALAY_MALAYSIA = 'ms-MY'
    MALTESE = 'mt'
    MALTESE_MALTA = 'mt-MT'
    NORWEGIAN_BOKMAL = 'nb'
    NORWEGIAN_BOKMAL_NORWAY = 'nb-NO'
    DUTCH = 'nl'
    DUTCH_BELGIUM = 'nl-BE'
    DUTCH_NETHERLANDS = 'nl-NL'
    NORWEGIAN_NYNORSK = 'nn'
    NORWEGIAN_NYNORSK_NORWAY = 'nn-NO'
    NORTHERN_SOTHO = 'ns'
    NORTHERN_SOTHO_SOUTH_AFRICA = 'ns-ZA'
    PUNJABI = 'pa'
    PUNJABI_INDIA = 'pa-IN'
    POLISH = 'pl'
    POLISH_POLAND = 'pl-PL'
    PASHTO = 'ps'
    PASHTO_AFGHANISTAN = 'ps-AR'
    PORTUGUESE = 'pt'
    PORTUGUESE_BRAZIL = 'pt-BR'
    PORTUGUESE_PORTUGAL = 'pt-PT'
    QUECHUA = 'qu'
    QUECHUA_BOLIVIA = 'qu-BO'
    QUECHUA_ECUADOR = 'qu-EC'
    QUECHUA_PERU = 'qu-PE'
    ROMANIAN = 'ro'
    ROMANIAN_ROMANIA = 'ro-RO'
    RUSSIAN = 'ru'
    RUSSIAN_RUSSIA = 'ru-RU'
    SANSKRIT = 'sa'
    SANSKRIT_INDIA = 'sa-IN'
    SAMI = 'se'
    SAMI_NORTHERN_FINLAND = 'se-FI'
    SAMI_SKOLT_FINLAND = 'se-FI'
    SAMI_INARI_FINLAND = 'se-FI'
    SAMI_NORTHERN_NORWAY = 'se-NO'
    SAMI_LULE_NORWAY = 'se-NO'
    SAMI_SOUTHERN_NORWAY = 'se-NO'
    SAMI_NORTHERN_SWEDEN = 'se-SE'
    SAMI_LULE_SWEDEN = 'se-SE'
    SAMI_SOUTHERN_SWEDEN = 'se-SE'
    SLOVAK = 'sk'
    SLOVAK_SLOVAKIA = 'sk-SK'
    SLOVENIAN = 'sl'
    SLOVENIAN_SLOVENIA = 'sl-SI'
    ALBANIAN = 'sq'
    ALBANIAN_ALBANIA = 'sq-AL'
    SERBIAN_LATIN_BOSNIA_HERZEGOVINA = 'sr-BA'
    SERBIAN_CYRILLIC_BOSNIA_HERZEGOVINA = 'sr-BA'
    SERBIAN_LATIN_SERBIA_MONTENEGRO = 'sr-SP'
    SERBIAN_CYRILLIC_SERBIA_MONTENEGRO = 'sr-SP'
    SWEDISH = 'sv'
    SWEDISH_FINLAND = 'sv-FI'
    SWEDISH_SWEDEN = 'sv-SE'
    SWAHILI = 'sw'
    SWAHILI_KENYA = 'sw-KE'
    SYRIAC = 'syr'
    SYRIAC_SYRIA = 'syr-SY'
    TAMIL = 'ta'
    TAMIL_INDIA = 'ta-IN'
    TELUGU = 'te'
    TELUGU_INDIA = 'te-IN'
    THAI = 'th'
    THAI_THAILAND = 'th-TH'
    TAGALOG = 'tl'
    TAGALOG_PHILIPPINES = 'tl-PH'
    TSWANA = 'tn'
    TSWANA_SOUTH_AFRICA = 'tn-ZA'
    TURKISH = 'tr'
    TURKISH_TURKEY = 'tr-TR'
    TATAR = 'tt'
    TATAR_RUSSIA = 'tt-RU'
    TSONGA = 'ts'
    UKRAINIAN = 'uk'
    UKRAINIAN_UKRAINE = 'uk-UA'
    URDU = 'ur'
    URDU_PAKISTAN = 'ur-PK'
    UZBEK_LATIN = 'uz'
    UZBEK_LATIN_UZBEKISTAN = 'uz-UZ'
    UZBEK_CYRILLIC_UZBEKISTAN = 'uz-UZ'
    VIETNAMESE = 'vi'
    VIETNAMESE_VIET_NAM = 'vi-VN'
    XHOSA = 'xh'
    XHOSA_SOUTH_AFRICA = 'xh-ZA'
    CHINESE = 'zh'
    CHINESE_CHINA = 'zh-CN'
    CHINESE_HONG_KONG = 'zh-HK'
    CHINESE_MACAU = 'zh-MO'
    CHINESE_SINGAPORE = 'zh-SG'
    CHINESE_TAIWAN = 'zh-TW'
    ZULU = 'zu'
    ZULU_SOUTH_AFRICA = 'zu-ZA'

    @staticmethod
    def validate(lang_code) -> bool:
        VALIDATE_METHOD_NAME = 'validate'
        MiniLogger.start(message=VALIDATE_METHOD_NAME, object={"lang_code": lang_code})
        if lang_code is not None and not isinstance(lang_code, LangCode):
            raise TypeError('lang_code must be an instance of LangCode or None')
        MiniLogger.end(message=VALIDATE_METHOD_NAME, object={"lang_code": lang_code})

    @staticmethod
    def lang_code_str_to_lang_code(lang_code_str: str) -> 'LangCode':
        return LangCode(lang_code_str)

    @staticmethod
    def detect_lang_code_str(text: str, attempts=3) -> str | None:
        logger = MiniLogger()
        name = "detect_lang_code_str"

        logger.start(message=name, object={"text": text, "attempts": attempts})

        if not text or not text.strip():
            logger.end(message=name, object={"result": None})
            return None

        try:
            results = [detect(text) for _ in range(attempts)]
            result, _ = Counter(results).most_common(1)[0]

            raw = result.lower()
            if '-' in raw:
                lang, country = raw.split('-', 1)
                normalized = f"{lang}-{country.upper()}"
            else:
                normalized = raw

            logger.end(message=name, object={"result": normalized})
            return normalized

        except LangDetectException as e:
            #logger.exception(message=name, object={"error": str(e)})
            logger.end(message=name, object={"result": None})
            return None



    @staticmethod
    def detect_lang_code(text: str, attempts=3) -> 'LangCode':
        DETECT_LANG_CODE_METHOD_NAME = 'detect_lang_code'
        MiniLogger.start(message=DETECT_LANG_CODE_METHOD_NAME, object={"text": text, "attempts": attempts})
        lang_code_str = LangCode.detect_lang_code_str(text, attempts)
        if lang_code_str is None:
            MiniLogger.end(message=DETECT_LANG_CODE_METHOD_NAME, object={"result": None})
            return None
        MiniLogger.end(message=DETECT_LANG_CODE_METHOD_NAME, object={"result": lang_code_str})
        return LangCode(lang_code_str)

    @staticmethod
    def detect_lang_code_restricted(text: str, allowed_lang_codes: list[str] = None, attempts: int = 3,
                                    default_lang_code: 'LangCode' = None) -> 'LangCode':
        DETECT_LANG_CODE_RESTRICTED_METHOD_NAME = 'detect_lang_code_restricted'
        MiniLogger.start(message=DETECT_LANG_CODE_RESTRICTED_METHOD_NAME,
                         object={"text": text, "allowed_lang_codes": allowed_lang_codes, "attempts": attempts})
        if allowed_lang_codes is None:
            default_allowed_lang_codes = [LangCode.ENGLISH.value, LangCode.RUSSIAN.value,
                                          LangCode.HEBREW.value, LangCode.ARABIC.value]
            MiniLogger.info(message="Allowed lang codes is None, using default allowed lang codes",
                            object={"allowed_lang_codes": allowed_lang_codes,
                                    "default_allowed_lang_codes": default_allowed_lang_codes})
            allowed_lang_codes = default_allowed_lang_codes
        lang_code_str = LangCode.detect_lang_code_str(text, attempts)
        if lang_code_str in allowed_lang_codes:
            MiniLogger.end(message=DETECT_LANG_CODE_RESTRICTED_METHOD_NAME, object={"result": lang_code_str})
            return LangCode(lang_code_str)
        MiniLogger.end(message=DETECT_LANG_CODE_RESTRICTED_METHOD_NAME, object={"result": None})
        return default_lang_code

    @staticmethod
    def detect_lang_code_str_restricted(text: str, allowed_lang_codes: list[str] = None, attempts: int = 3,
                                        default_lang_code: str = None) -> str:
        DETECT_LANG_CODE_STR_RESTRICTED_METHOD_NAME = 'detect_lang_code_str_restricted'
        MiniLogger.start(message=DETECT_LANG_CODE_STR_RESTRICTED_METHOD_NAME,
                         object={"text": text, "allowed_lang_codes": allowed_lang_codes, "attempts": attempts})
        if allowed_lang_codes is None:
            default_allowed_lang_codes = [LangCode.ENGLISH.value, LangCode.RUSSIAN.value,
                                          LangCode.HEBREW.value, LangCode.ARABIC.value,
                                          LangCode.FRENCH.value, LangCode.GERMAN.value,
                                          LangCode.SPANISH.value, LangCode.ITALIAN.value]
            MiniLogger.info(message="Allowed lang codes is None, using default allowed lang codes",
                            object={"allowed_lang_codes": allowed_lang_codes,
                                    "default_allowed_lang_codes": default_allowed_lang_codes})
            allowed_lang_codes = default_allowed_lang_codes
        lang_code_str = LangCode.detect_lang_code_str(text, attempts)
        if lang_code_str in allowed_lang_codes:
            MiniLogger.end(message=DETECT_LANG_CODE_STR_RESTRICTED_METHOD_NAME, object={"result": lang_code_str})
            return lang_code_str
        MiniLogger.end(message=DETECT_LANG_CODE_STR_RESTRICTED_METHOD_NAME, object={"result": default_lang_code})
        return default_lang_code

    # Is the language written from right to left
    '''
    Check if the language is written from right to left
    :param lang_code: LangCode (optional)
    :param lang_code_str: str (optional)
    :return: bool
    Examples:
    is_language_rtl(lang_code=LangCode.ARABIC) -> True
    is_language_rtl(lang_code_str="he") -> True
    is_language_rtl(lang_code=LangCode.ENGLISH) -> False
    is_language_rtl(lang_code_str="fr") -> False
    '''
    @staticmethod
    def is_language_rtl(*, lang_code: 'LangCode' = None, lang_code_str: str = None) -> bool:
        IS_LANGUAGE_RTL_METHOD_NAME = 'is_language_rtl'
        MiniLogger.start(message=IS_LANGUAGE_RTL_METHOD_NAME, object={"lang_code": lang_code, "lang_code_str": lang_code_str})
        if lang_code is not None:
            lang_code_str = lang_code.value
        if lang_code_str is None:
            MiniLogger.end(message=IS_LANGUAGE_RTL_METHOD_NAME, object={"result": False})
            return False
        result = lang_code_str in [LangCode.ARABIC.value, LangCode.HEBREW.value, LangCode.URDU.value, LangCode.FARSI.value]
        MiniLogger.end(message=IS_LANGUAGE_RTL_METHOD_NAME, object={"result": result})
        return result
