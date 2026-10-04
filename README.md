# vacancy_project

A Django website that collects junior Python job vacancies from several job sites. Visitors can read them, registered users can filter them and track their own applications.

Sources: Jooble, Work.ua, DOU.ua. Robota.ua is disabled (see "Known limits").

---

##  Features

**Guest (no registration)**
- Choose one source and see its vacancies.
- Start parsing of that one source.

**Registered user**
- See vacancies from all sources.
- Mark a vacancy as "applied" or "not relevant". Statuses are private: every user has their own.
- Filter by source and by status (all, applied, not applied, not relevant).
- Start parsing of one source or of all sources.

**Protection**
- Pause of 10 minutes between two runs of the same source.
- Only one run per source at the same time (enforced by a database constraint).
- Every run is saved in the `ParseRun` table (who, when, result).
- The admin button "Запустити парсери" is only for superusers.

---

##  Getting Started

### 1. Install

```bash
pip install -r requirements.txt
```

Create a `.env` file (see "Configuration").

### 2. Create the database tables

```bash
python manage.py migrate
```

### 3. Create an administrator

```bash
python manage.py createsuperuser
```

### 4. Run the site

```bash
python manage.py runserver
```

### 5. Run the scrapers from the command line (optional)

```bash
python manage.py run_all
```

One broken source does not stop the others. Errors are written to the log.

### 6. Run the Telegram bot (optional)

```bash
python manage.py run_bot
```

---

##  Configuration

PostgreSQL is used as the database. Secrets are stored in the `.env` file:

```env
V_SECRET_KEY=your_django_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=...

JOOBLE_API_KEY=your_api_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

> Never commit `.env` to git.

Work.ua is scraped with a real browser (Selenium), so Google Chrome must be installed on the machine.

---

##  Architecture

Each layer does one job:

| Layer | File | Job |
|---|---|---|
| Parsers | `jobs/parsers/*.py` | Get raw vacancies from a site. They never write to the database. |
| Registry | `jobs/parsers/registry.py` | One place that maps a source to its parser. |
| Filters | `jobs/filters.py` | Shared rules: how old, junior or not, Python or not. |
| Selectors | `jobs/selectors.py` | Read data from the database. |
| Services | `jobs/services.py` | Change data: save vacancies, set statuses, start parsing. Uses transactions. |
| Models | `jobs/models.py` | `Vacancy`, `UserVacancy`, `ParseRun`. |
| Views | `jobs/views.py`, `accounts/views.py` | Take a request, return a page. They contain no business logic. |
| Errors | `jobs/exceptions.py` | `ParserError`: a site could not be read. `ParseNotAllowed`: parsing cannot start now. |

An empty list from a parser means "nothing new". A `ParserError` means "something broke".

### Filters

- A vacancy must be at most 7 days old.
- Level: the title is more important than the description. A junior word in the title is good, a senior word in the title is bad. If the title has no level, the description is checked. No level anywhere is also good.
- Some sites already filter in the URL or API (DOU: experience, remote, Python. Work.ua: remote, Python). Those checks are not repeated in code.

---

##  Project Structure

```
vacancy_project/
│
├── jobs/                       # Vacancies
│   ├── admin.py                # Admin: vacancies, parse runs
│   ├── models.py               # Vacancy, UserVacancy, ParseRun
│   ├── selectors.py            # Read queries
│   ├── services.py             # Save vacancies, statuses, start parsing
│   ├── filters.py              # Shared filter rules
│   ├── exceptions.py           # ParserError, ParseNotAllowed
│   ├── views.py                # Vacancy list, status buttons, parse buttons
│   ├── management/commands/
│   │   ├── run_all.py          # Run all parsers
│   │   └── run_bot.py          # Run the Telegram bot
│   ├── migrations/             # Database migrations (keep them in git)
│   └── parsers/
│       ├── registry.py         # source -> parser
│       ├── dou.py              # RSS feed
│       ├── jooble.py           # API
│       ├── work.py             # Selenium
│       ├── robota.py           # Playwright (disabled)
│       └── indeed.py           # Not connected yet
│
├── accounts/                   # Registration, login, logout
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── telegram_bot/
│   └── bot.py
│
├── templates/
│   ├── base.html
│   ├── jobs/vacancy_list.html
│   ├── accounts/               # register.html, login.html
│   └── admin/jobs/vacancy/change_list.html
│
├── vacancy_project/            # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── .env                        # Secrets (not in git)
├── manage.py
├── Procfile                    # Render start command
└── README.md
```

---

##  Known limits

- **Robota.ua is disabled.** Cloudflare asks "confirm you are human" and blocks the automatic browser.
- **Indeed** has a parser file, but it is not connected.
- **Work.ua needs Chrome.** It is usually not installed on Render, so there this parser reports an error and the other sources still work.
- **Telegram bot** still uses the old shared statuses on `Vacancy`, not the personal `UserVacancy` statuses.
- Keyword filters cannot read the full text of a vacancy.
- Parsing runs in a background thread. A server restart can interrupt a run (such a run is closed automatically after 15 minutes).

---

## ️ Planned

- Parsing options: how many last days, keyword.
- Users in the admin panel with editing.
- Tests and GitHub Actions.
- Telegram bot on personal statuses.
- AI helper that checks how well a vacancy matches.

---

##  Deployment (Render)

- **Start command:** see `Procfile` (gunicorn).
- Build Command: pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
- Behind the Render proxy the settings use `SECURE_PROXY_SSL_HEADER` and `CSRF_TRUSTED_ORIGINS`, otherwise forms fail with a CSRF error.
- Local and Render use the same Supabase PostgreSQL database, so be careful with deleting data.

Live site: [https://vacancy-project.onrender.com/](https://vacancy-project.onrender.com/)
