from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Vacancy
from .selectors import VALID_STATUSES, get_available_sources, get_vacancies
from .services import STATUS_FIELDS, set_vacancy_status


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