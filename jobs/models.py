# jobs\models.py

from django.db import models

class Vacancy(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="Remote")
    link = models.URLField()
    source = models.CharField(max_length=50)  # Jooble, Indeed, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)  # чи відгукнувся
    is_sent = models.BooleanField(default=False) # чи відправлено у Telegram

    def __str__(self):
        return f"{self.title} @ {self.company}"

    @classmethod
    def save_to_db(cls, source_name: str, vacancies: list[dict]):
        """Запис знайдених вакансій в базу даних"""
        saved = []
        for v in vacancies:
            vacancy, created = cls.objects.get_or_create(
                link=v["link"],
                defaults={
                    "title": v["title"],
                    "company": v["company"],
                    "location": v.get("location", "Remote"),
                    "source": source_name,
                    "is_sent": False,
                },
            )
            if created:
                saved.append(vacancy)
        return saved
