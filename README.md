# vacancy_project

A Django website that collects junior Python job vacancies from several job sites. 
Visitors can read them, registered users can filter them and track their own applications.

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

### 2. Create your `.env` file

Copy the example file and fill in your own values (see "Configuration" below):

```bash
cp .env.example .env
```

On Windows PowerShell: `Copy-Item .env.example .env`

### 3. Create the database tables

```bash
python manage.py migrate
```

### 4. Create an administrator

```bash
python manage.py createsuperuser
```

### 5. Run the site

```bash
python manage.py runserver
```

### 6. Run the scrapers from the command line (optional)

```bash
python manage.py run_all
```

One broken source does not stop the others. Errors are written to the log.

### 7. Run the Telegram bot (optional)

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


### Filters

- A vacancy must be at most 7 days old.
- Level: the title is more important than the description. A junior word in the title is good, 
  a senior word in the title is bad. If the title has no level, the description is checked. 
  No level anywhere is also good.
- Some sites already filter in the URL or API (DOU: experience, remote, Python. Work.ua: remote, Python). 
  Those checks are not repeated in code.

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
├── .env                        # Real secrets (not in git)
├── .env.example                # Placeholder secrets values
├── manage.py
├── Procfile                    # Start command for Heroku-style hosts (Render uses its own Start Command)
└── README.md
```

---

##  Known limits

- **Robota.ua is disabled.** Cloudflare asks "confirm you are human" and blocks the automatic browser.
- **Indeed** has a parser file, but it is not connected.
- **Work.ua needs Chrome.** It is usually not installed on Render, so there this parser reports an error 
    and the other sources still work.
- **Telegram bot** still uses the old shared statuses on `Vacancy`, not the personal `UserVacancy` statuses.
- Keyword filters cannot read the full text of a vacancy.
- Parsing runs in a background thread. A server restart can interrupt a run 
  (such a run is closed automatically after 15 minutes).

---

## ️ Planned

- Parsing options: how many last days, keyword.
- Users in the admin panel with editing.
- Tests and GitHub Actions.
- Telegram bot on personal statuses.
- AI helper that checks how well a vacancy matches.

---

##  Deployment (Render, free plan)

The site runs as a Render **Web Service** on the free plan. It is connected to this GitHub repository (branch `master`). 
Every commit starts a new deploy automatically (Auto-Deploy: On Commit).

### Service settings

| Setting | Value |
|---|---|
| Build Command | `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` |
| Start Command | `gunicorn vacancy_project.wsgi` |

- **Build Command** installs packages, applies database migrations and collects static files (served by WhiteNoise). 
    Migrations run on every deploy, so tables are always up to date.
- **Start Command** starts the web server.

### Environment variables

Set these in the Render dashboard (Environment). Never put real values in git.

`V_SECRET_KEY`, `DEBUG` (`False`), `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, 
`JOOBLE_API_KEY`, `TELEGRAM_BOT_TOKEN`

Live site: [https://vacancy-project.onrender.com/](https://vacancy-project.onrender.com/)