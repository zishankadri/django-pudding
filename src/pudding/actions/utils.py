def is_htmx(request):
    return request.META.get("HTTP_HX_REQUEST") == "true"
