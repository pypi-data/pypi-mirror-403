from secrets import choice
from string import ascii_letters, digits, punctuation
from .config import Config


def generate_password(length: int = None):
    config = Config()

    if length is None:
        length = config.default_password_length

    chars = (ascii_letters if config.password_ascii else "") + (digits if config.password_digits else "") + (punctuation if config.password_punctuation else "")

    return ''.join(choice(chars) for _ in range(length))