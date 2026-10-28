from datetime import timedelta, datetime

from jobs.constants import DEFAULT_DAYS
from jobs.filters import is_recent, is_junior_level, is_python


class TestIsRecent:
    def test_recent_vacancy(self):
        test_date = datetime.now() - timedelta(days=DEFAULT_DAYS)
        assert is_recent(test_date, DEFAULT_DAYS) is True

    def test_old_vacancy(self):
        test_date = datetime.now() - timedelta(days=DEFAULT_DAYS + 1)
        assert is_recent(test_date, DEFAULT_DAYS) is False


class TestIsJuniorLevel:
    def test_returns_true_when_junior_in_title_even_with_senior(self):
        assert is_junior_level("Junior/Senior Python Developer") is True

    def test_returns_false_when_senior_word_in_title(self):
        assert is_junior_level("Senior Python developer") is False

    def test_returns_true_when_junior_in_description_even_with_senior(self):
        assert is_junior_level("Python Developer", "junior or senior") is True

    def test_returns_false_when_senior_word_in_description(self):
        assert is_junior_level("Python Developer", "senior") is False

    def test_returns_true_when_not_level_anywhere(self):
        assert is_junior_level("Developer", "developer") is True


class TestIsPython:
    def test_returns_true_when_python_in_title(self):
        assert is_python("junior python developer") is True

    def test_returns_false_when_python_not_mentioned(self):
        assert is_python("Junior Java Developer") is False
