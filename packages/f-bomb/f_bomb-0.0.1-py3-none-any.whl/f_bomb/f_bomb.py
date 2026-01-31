

FUCK = {
    "en": "fuck",            # The strongest common English profanity, sexual in origin and broadly offensive.
    "es": "coño",            # A vulgar sexual term widely used as a harsh expletive across Spanish dialects.
    "fr": "putain",          # A profane term meaning “whore,” used forcefully to express anger or shock.
    "de": "scheiße",         # A blunt scatological insult and one of the strongest everyday German curses.
    "it": "cazzo",           # A crude sexual term used aggressively as an expletive.
    "pt": "caralho",         # A highly vulgar sexual term considered stronger than most Portuguese curses.
    "nl": "kut",             # A direct genital reference and among the most offensive Dutch expletives.
    "sv": "fan",             # Short for “the devil,” used as a strong Swedish profanity.
    "no": "faen",            # Derived from “the devil,” considered a strong Norwegian curse.
    "da": "for helvede",     # Invokes hell directly and is a serious Danish profanity.
    "fi": "vittu",           # A very strong Finnish sexual swear word with high taboo weight.
    "is": "andskotinn",      # Invokes damnation and is one of Iceland’s strongest curses.
    "ru": "блядь",           # An extremely vulgar sexual slur and one of the strongest Russian expletives.
    "uk": "блядь",           # Same root and severity as Russian, highly offensive.
    "pl": "kurwa",           # A deeply vulgar term meaning “whore,” used forcefully as an expletive.
    "cs": "kurva",           # A strong sexual slur and one of Czech’s harshest swear words.
    "sk": "kurva",           # Identical usage and offensiveness to Czech.
    "sl": "pizda",           # A crude genital term and among Slovenia’s strongest profanities.
    "hr": "jebote",          # A blasphemous sexualized expletive with high offensiveness.
    "sr": "jebote",          # Same construction and severity as Croatian usage.
    "bg": "мамка му",        # An aggressive insult involving one’s mother, very offensive culturally.
    "mk": "пичка му матер",  # An extremely crude maternal/genital insult.
    "el": "γαμώ",            # A direct sexual verb used as a powerful Greek expletive.
    "ro": "futu-i",          # A sexually explicit curse invoking intercourse, highly offensive.
    "hu": "bazdmeg",         # A notoriously strong Hungarian sexual profanity.
    "ar": "كس أمك",          # A highly offensive maternal/genital insult in Arabic.
    "he": "זין",             # A crude sexual term used aggressively as a curse.
    "fa": "کیر",             # A direct sexual reference considered extremely vulgar.
    "hi": "मादरचोद",         # A severe incest-based insult and one of Hindi’s strongest curses.
    "ur": "ماں چود",         # Equivalent severity and meaning to the Hindi form.
    "bn": "মাগী",            # A strong sexual slur used aggressively.
    "ja": "くそ",             # Literally “shit,” the strongest commonly used Japanese expletive.
    "ko": "씨발",            # The most offensive common Korean swear word, sexual in origin.
    "zh": "操你妈",           # An extremely vulgar maternal/sexual insult in Mandarin.
    "th": "เหี้ย",            # A highly offensive animal-based curse in Thai.
    "vi": "địt mẹ",          # A very strong sexual insult involving one’s mother.
    "id": "anjing",          # A harsh insult meaning “dog,” strong in Indonesian context.
    "ms": "babi",            # A deeply offensive insult meaning “pig.”
    "sw": "fuck",            # Borrowed English profanity, considered very strong in Swahili contexts.
    "am": "ደንቆሮ",           # A severe insult implying worthlessness or stupidity.
    "af": "poes",            # A crude sexual term and one of Afrikaans’ strongest curses.
    "tr": "amına koyayım",   # A highly explicit sexual curse, extremely offensive.
    "ka": "დედის მუტელი",     # A strong maternal/genital insult in Georgian.
    "et": "perse",           # A crude sexual reference and strong Estonian profanity.
    "lv": "pizda",           # A direct genital term and very offensive Latvian curse.
    "lt": "pizda",           # Same root and severity as Latvian usage.
}

class F_Bomb:

    def __init__(self, language: str = "en"):
        self.language = language.lower()

    def drop(self, language: str = None):
        """
        Drops a formatted string based on the specified language. If no language is provided, uses
        the default language assigned to the instance.

        :param language: Optional; a string representing the language to drop. If provided, the value
            will be converted to lowercase before use.
        :return: A formatted uppercase string for the specified or default language.
        :rtype: str
        """
        if language is not None:
            language = language.lower()
            return f"{FUCK[language].upper()}!"

        return f"{FUCK[self.language].upper()}!"

    def carpet_bomb(self, number: int = 100, language: str = None):
        """
        Executes a repetitive concatenation of the results from the `drop` method
        based on the specified `number`, separated by newline characters. This
        method provides a way to produce a bulk output with a customizable count
        and optional language setting.

        :param number: The number of newline-separated repetitions for the output. Defaults to 100.
        :type number: int
        :param language: An optional parameter to specify the language for the `drop` method. Defaults to None.
        :type language: str
        :return: A concatenated string containing the results of the `drop` method, repeated `number` times,
            with newline characters separating each repetition.
        :rtype: str
        """
        return self.drop(language) + "\n" * number


    def __str__(self):
        return self.drop()

    def __repr__(self):
        return self.__str__()
