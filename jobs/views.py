from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .exceptions import ParseNotAllowed
from .models import Vacancy
from .selectors import VALID_STATUSES, get_available_sources, get_last_run, get_vacancies
from .services import STATUS_FIELDS, set_vacancy_status, start_parse, start_parse_all


def vacancy_list(request):
    sources = get_available_sources()
    valid = {value for value, _ in sources}

    # Never trust the URL: accept only known sources.
    source = request.GET.get("source", "")
    if source not in valid:
        source = ""

    # Same rule for status: only known values.
    status = request.GET.get("status", "all")
    if status not in VALID_STATUSES:
        status = "all"

    # A guest always sees exactly one source.
    if not request.user.is_authenticated and not source and sources:
        source = sources[0][0]

    paginator = Paginator(get_vacancies(request.user, source or None, status), 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "jobs/vacancy_list.html", {
        "page_obj": page_obj,
        "sources": sources,
        "source": source,
        "status": status,
        "last_run": get_last_run(source) if source else None,
    })


@login_required
@require_POST
def set_status(request, vacancy_id):
    """Change the status of one vacancy for the current user."""
    # Accept only known actions.
    action = request.POST.get("action", "")
    if action not in STATUS_FIELDS:
        return HttpResponseBadRequest("Unknown action")

    vacancy = get_object_or_404(Vacancy, pk=vacancy_id)
    # The user comes from the session, never from the form.
    set_vacancy_status(request.user, vacancy, action)

    # Go back to the same page, but only to our own site (no open redirect).
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "home"
    return redirect(next_url)


@require_POST
def run_parse(request):
    """Start parsing of one source. Allowed for guests too."""
    source = request.POST.get("source", "")
    try:
        start_parse(request.user, source)
    except ParseNotAllowed as e:
        # The text is written by us, so it is safe to show.
        messages.error(request, str(e))
    else:
        messages.success(request, "Парсинг запущено. Оновіть сторінку за хвилину.")
    return redirect("home")


@login_required
@require_POST
def run_parse_all(request):
    """Start parsing of all sources. Only for logged-in users."""
    started, skipped = start_parse_all(request.user)
    if started:
        messages.success(request, f"Запущено: {', '.join(started)}. Оновіть сторінку за хвилину.")
    for text in skipped:
        messages.warning(request, text)
    return redirect("home")