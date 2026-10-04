from jobs.models import Vacancy
from jobs.parsers.dou import fetch_dou_rss
from jobs.parsers.jooble import fetch_joobl
from jobs.parsers.work import fetch_work

# Robota is not here: it is disabled (Cloudflare).
PARSERS = {
    Vacancy.Source.JOOBLE.value: fetch_joobl,
    Vacancy.Source.WORK.value: fetch_work,
    Vacancy.Source.DOU.value: fetch_dou_rss,
}