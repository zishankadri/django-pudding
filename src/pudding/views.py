from django.contrib import messages
from django.http import HttpRequest, HttpResponse

from pudding import domains
from pudding.exceptions import PermissionDenied


def run_action(request: HttpRequest, domain_slug: str, action_slug: str):
    domain = domains.get(domain_slug)
    action = domain.get_action(action_slug)

    if action.permission and not action.permission(request):
        raise PermissionDenied("You do not have permission to perform this action.")

    if not domain.has_permission(request=request, action=action):
        raise PermissionDenied("You do not have permission to perform this action.")

    if not action:
        messages.error(request, "Invalid action.")
        response = HttpResponse()
        response["HX-Redirect"] = request.META.get("HTTP_REFERER", "/")
        return response

    ids = request.POST.getlist("pks[]") or request.GET.getlist("pks[]")

    ctx: dict[str, object] = {
        "request": request,
        "domain": domain,
    }

    if domain.model is not None:
        ctx["queryset"] = domain.model._default_manager.filter(pk__in=ids)

    return action.handle(request=request, ctx=ctx)
