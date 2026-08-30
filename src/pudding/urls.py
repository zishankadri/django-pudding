from django.urls import path

from . import views

app_name = "pudding"

urlpatterns = [
    path(
        "<str:domain_slug>/<str:action_slug>/",
        views.run_action,
        name="run_action",
    ),
]
