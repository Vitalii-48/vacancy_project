class ParserError(Exception):
    """Парсер не зміг отримати дані з джерела."""


class ParseNotAllowed(Exception):
    """Parsing cannot start now (cooldown or already running).
    The text is safe to show to the user."""