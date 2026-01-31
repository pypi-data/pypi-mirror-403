from django.urls import path

from . import views

app_name = "nui"
urlpatterns = [
    path("", views.index, name="index"),
    path("collection/<int:collection_id>", views.collection, name="collection"),
    path(
        "collection/<int:collection_id>/resource/<int:resource_id>",
        views.resource,
        name="resource",
    ),
    path("search", views.search, name="search"),
    path(
        "project/<int:project_id>/",
        views.project_manage,
        name="project_manage",
    ),
    path(
        "project/<int:project_id>/add_user_to_project/",
        views.add_user_to_project,
        name="add_user_to_project",
    ),
    # path("test", views.test),
]
