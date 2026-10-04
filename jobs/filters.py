from datetime import datetime, timedelta

# Vacancies older than this many days are ignored.
MAX_AGE_DAYS = 7

# Words that mean "this job is for a beginner".
JUNIOR_WORDS = {
    "junior", "trainee", "intern",
    "стажер", "стажист", "джуніор", "джун", "юніор",
}

# Words that mean "this job is for an experienced person".
SENIOR_WORDS = {
    "middle", "mid", "senior", "lead", "staff",
    "мідл", "сеньйор", "сеніор", "тімлід", "тимлід",
}


def _words(text: str) -> set[str]:
    """Split text into separate lowercase words, without punctuation."""
    # Replace every symbol that is not a letter or a digit with a space.
    cleaned = "".join(ch if ch.isalnum() else " " for ch in text.lower())
    return set(cleaned.split())


def is_recent(published: datetime) -> bool:
    """Return True if the vacancy is not older than MAX_AGE_DAYS days."""
    return published >= datetime.now() - timedelta(days=MAX_AGE_DAYS)


def is_junior_level(title: str, snippet: str = "") -> bool:
    """Return True if the vacancy is suitable for a junior.

    The title is more important than the description:
    1. Junior word in title: good.
    2. Senior word in title: bad.
    3. No level in title, junior word in description: good.
    4. No level in title, senior word in description: bad.
    5. No level anywhere: good.
    """
    title_words = _words(title)
    if not JUNIOR_WORDS.isdisjoint(title_words):  # any junior word in title
        return True
    if not SENIOR_WORDS.isdisjoint(title_words):  # any senior word in title
        return False

    snippet_words = _words(snippet)
    if not JUNIOR_WORDS.isdisjoint(snippet_words):
        return True
    # Good only if there is no senior word in the description.
    return SENIOR_WORDS.isdisjoint(snippet_words)


def is_python(title: str, snippet: str = "") -> bool:
    """Return True if the word 'python' is in the title or description."""
    return "python" in f"{title} {snippet}".lower()