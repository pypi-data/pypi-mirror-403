from typing import List
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse, Http404
from resources.models import (
    ProjectAccess,
    Collection,
    Project,
    Resource,
    Metadata,
    MetadataResourceValue,
    Role,
    Permission,
)
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.cache import never_cache
from rpc.methods import _user_has_permission as user_has_permission
from django.contrib.auth.models import User, AbstractUser
from rpc.const import PERM_RESOURCE_UPDATE
from functools import cache
from django.conf import settings

RESOURCES_PAGES_SIZE = 500


def _admin_check(user: AbstractUser) -> bool:
    return user.is_superuser


def editable_metadatas(project: Project) -> List[Metadata]:
    return (
        Metadata.objects.filter(project=project)
        .exclude(set__title__in=["ExifTool", "OCR"])
        .order_by("set", "title")
        .select_related("set")
    )


def user_has_project_access(user: User, project: Project) -> bool:
    if not ProjectAccess.objects.filter(project=project, user=user).first():
        raise PermissionDenied()
    return True


@login_required
@never_cache
def index(request: HttpRequest) -> HttpResponse:
    if request.method == "POST" and request.POST.get("action") == "add_project":
        project_name = request.POST.get("project_name", "").strip()
        project = Project.objects.filter(label__iexact=project_name).first()
        if not project:
            project = Project.objects.create(label=project_name)
    ui_is_available = False
    if "ui" in settings.AUTO_REGISTER_APPS:
        ui_is_available = True
    return render(
        request,
        "nui/index.html",
        {
            "projects": Project.objects.order_by("label").iterator(),
            "ui_is_available": ui_is_available,
        },
    )


@login_required
@never_cache
def collection(request: HttpRequest, collection_id: int) -> HttpResponse:
    collection_instance: Collection = get_object_or_404(Collection, pk=collection_id)
    project_instance = collection_instance.project
    user_has_project_access(request.user, project_instance)
    resources = (
        collection_instance.resources.filter(deleted_at__isnull=True)
        .order_by("collectionmembership__rank", "title")
        .select_related("file")
    )
    resources_paginator = Paginator(resources, RESOURCES_PAGES_SIZE)
    try:
        page_number = int(request.GET.get("page", 1))
    except ValueError:
        page_number = 1
    try:
        resources_page = resources_paginator.page(page_number)
    except EmptyPage:
        resources_page = None
    return render(
        request,
        "nui/collection.html",
        {
            "collection": collection_instance,
            "project": project_instance,
            "resources_page": resources_page,
            "page_number": page_number,
        },
    )


def _fetch_resource(resource_id: int) -> Resource:
    return (
        Resource.objects.filter(pk=resource_id, deleted_at__isnull=True)
        .prefetch_related(
            "metadataresourcevalue_set",
            "metadataresourcevalue_set__metadata",
            "metadataresourcevalue_set__metadata__set",
        )
        .first()
    )


@login_required
@never_cache
def resource(
    request: HttpRequest, collection_id: int, resource_id: int
) -> HttpResponse:
    collection_instance: Collection = get_object_or_404(
        Collection, pk=collection_id, deleted_at__isnull=True
    )
    transient_message = ""
    resource_instance = _fetch_resource(resource_id)
    if not resource_instance:
        raise Http404()
    project_instance = resource_instance.ptr_project
    user_has_project_access(request.user, project_instance)
    user_has_update_permission = user_has_permission(
        request.user, project_instance, PERM_RESOURCE_UPDATE
    )
    if request.method == "POST" and user_has_update_permission:
        for key in request.POST.keys():
            new_title = request.POST.get("resource_title", "").strip()
            if new_title:
                resource_instance.title = new_title
                resource_instance.save()
            if "_" in key:
                parts = key.split("_")
                try:
                    int(parts[1])
                except ValueError:
                    continue
                if parts[0] == "addvalue":
                    metadata = Metadata.objects.get(
                        pk=parts[1], project=project_instance
                    )
                    for val in request.POST.getlist(key):
                        MetadataResourceValue.objects.get_or_create(
                            resource=resource_instance,
                            metadata=metadata,
                            value=val.strip(),
                        )
                if parts[0] == "changevalue":
                    new_val = request.POST.get(key).strip()
                    metaval = MetadataResourceValue.objects.filter(
                        pk=parts[1], resource=resource_instance
                    ).first()
                    if metaval and new_val != metaval.value:
                        metaval.value = new_val
                        metaval.save()
                if parts[0] == "deletevalue":
                    metaval = MetadataResourceValue.objects.get(
                        pk=parts[1], resource=resource_instance
                    )
                    metaval.delete()
        resource_instance = _fetch_resource(resource_id)  # reload metas
        transient_message = "Resource enregistrée"

    previous_resource = None
    next_resource = None
    ids_list = list(
        collection_instance.resources.filter(deleted_at__isnull=True)
        .order_by("collectionmembership__rank", "title")
        .values_list("id", flat=True)
    )
    for i in range(len(ids_list)):
        if ids_list[i] == resource_instance.pk:
            if ids_list[i - 1] != ids_list[-1]:
                previous_resource = Resource.objects.get(pk=ids_list[i - 1])
            if i < len(ids_list) - 1:
                next_resource = Resource.objects.get(pk=ids_list[i + 1])

    return render(
        request,
        "nui/resource.html",
        {
            "resource": resource_instance,
            "collection": collection_instance,
            "project": project_instance,
            "previous_resource": previous_resource,
            "next_resource": next_resource,
            "editable_metadatas": editable_metadatas(project_instance),
            "user_has_update_permission": user_has_update_permission,
            "transient_message": transient_message,
        },
    )


def search(request: HttpRequest) -> HttpResponse:
    collection_search = Collection.objects.filter(
        title__icontains=request.GET.get("q")
    ).order_by("title")
    resource_search = Resource.objects.filter(
        title__icontains=request.GET.get("q")
    ).order_by("title")
    return render(
        request,
        "nui/search.html",
        {"collection_search": collection_search, "resource_search": resource_search},
    )


def _sids_jama_read_permissions() -> List[Permission]:
    perms = []
    for perm in Permission.objects.all():
        if ".read" in perm.label or perm.label == "file.download_source":
            perms.append(perm)
    return perms


def _sids_jama_write_permissions() -> List[Permission]:
    perms = []
    for perm in Permission.objects.all():
        if (
            ".update" in perm.label
            or ".create" in perm.label
            or perm.label == "file.upload"
        ):
            perms.append(perm)
    return perms


@cache
def _jama_read_role(project: Project) -> Role:
    role, _ = Role.objects.get_or_create(label="read", project=project)
    for perm in _sids_jama_read_permissions():
        role.permissions.add(perm)
    return role


@cache
def _jama_readwrite_role(project: Project) -> Role:
    role, _ = Role.objects.get_or_create(label="readwrite", project=project)
    for perm in _sids_jama_write_permissions():
        role.permissions.add(perm)
    for perm in _sids_jama_read_permissions():
        role.permissions.add(perm)
    return role


def _remove_user_from_project(project: Project, user: User):
    ProjectAccess.objects.filter(project=project, user=user).delete()


def _add_user_to_project(project: Project, user: User):
    _remove_user_from_project(project, user)
    ProjectAccess.objects.create(
        project=project, user=user, role=_jama_readwrite_role(project)
    )
    user.is_active = True
    user.save()


@never_cache
@user_passes_test(_admin_check)
def project_manage(request: HttpRequest, project_id: int) -> HttpResponse:
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST" and request.POST.get("action") == "remove_access":
        user = get_object_or_404(User, pk=request.POST.get("user_id"))
        _remove_user_from_project(project, user)
    return render(request, "nui/project_manage.html", {"project": project})


@never_cache
@user_passes_test(_admin_check)
def add_user_to_project(request: HttpRequest, project_id: int) -> HttpResponse:
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        user = get_object_or_404(User, pk=request.POST.get("user"))
        _add_user_to_project(project, user)
        return redirect(
            reverse("nui:project_manage", kwargs={"project_id": project.pk})
        )
    return render(
        request,
        "nui/add_user_to_project.html",
        {
            "project": project,
            "users": User.objects.exclude(projectaccess__project=project).order_by(
                "username"
            ),
        },
    )
