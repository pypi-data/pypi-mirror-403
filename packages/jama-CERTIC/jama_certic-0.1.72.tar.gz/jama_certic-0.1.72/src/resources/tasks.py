from huey.contrib.djhuey import db_task, db_periodic_task
from huey import crontab
import logging
from typing import List
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import connection
from resources import models
import os
import time
import shutil
import hashlib
from PIL import UnidentifiedImageError
from PIL.Image import DecompressionBombError

logger = logging.getLogger(__name__)


@db_task()
def exif_task(file_id: int):
    from resources.models import File
    from resources.helpers import set_exif_metas

    try:
        f = File.objects.get(pk=file_id)
        set_exif_metas(f)
    except Exception as e:
        logger.warning("exit_task({}) failed".format(file_id))
        logger.info(repr(e))


@db_task(retries=2, retry_delay=600)
def iiif_task(file_id: int):
    from resources.models import File
    from resources.helpers import make_iiif

    try:
        f = File.objects.get(pk=file_id)
        make_iiif(f, True)
    except Exception as e:
        logger.warning("iiif_task({}) failed: {}".format(file_id, repr(e)))
        raise e


@db_task(retries=2, retry_delay=600)
def hls_task(file_id: int):
    from resources.models import File
    from resources.helpers import make_hls

    try:
        f = File.objects.get(pk=file_id)
        make_hls(f, True)
    except Exception as e:
        logger.warning("hls_task({}) failed: {}".format(file_id, repr(e)))
        raise e


@db_task()
def ocr_task(file_id: int):
    from resources.models import File
    from resources.helpers import make_ocr

    try:
        f = File.objects.get(pk=file_id)
        make_ocr(f)
    except Exception as e:
        logger.warning("ocr_task({}) failed".format(file_id))
        logger.info(repr(e))


@db_task(retries=2, retry_delay=600)
def set_ark_to_resource(resource_id: int, location: str = None):
    if settings.ARK_SERVER and settings.ARK_APP_ID and settings.ARK_SECRET_KEY:
        from resources.models import Resource

        resource = Resource.objects.filter(pk=resource_id).first()
        if not resource:
            logger.warning(f"resource {resource_id} does not exist")
            return
        if resource.ark and not location:
            logger.info(f"resource {resource_id} has ark already, no update needed.")
            return
        import ark_client

        if not location:
            base_url = (
                settings.JAMA_SITE[:-1]
                if settings.JAMA_SITE[-1] == "/"
                else settings.JAMA_SITE
            )
            location = base_url + reverse(
                "ark_resource", kwargs={"resource_id": resource_id}
            )
        client = ark_client.Client(
            settings.ARK_APP_ID, settings.ARK_SECRET_KEY, settings.ARK_SERVER
        )
        if resource.ark:
            client.update(resource.ark, location)
        else:
            ark_name = client.create(location)
            resource.ark = ark_name
            Resource.objects.filter(pk=resource.pk).update(ark=ark_name)


@db_task(retries=2, retry_delay=600)
def set_ark_to_collection(collection_id: int, location: str = None):
    if settings.ARK_SERVER and settings.ARK_APP_ID and settings.ARK_SECRET_KEY:
        from resources.models import Collection

        collection = Collection.objects.filter(pk=collection_id).first()
        if not collection:
            logger.warning(f"collection {collection_id} does not exist")
            return
        if collection.ark and not location:
            logger.info(
                f"collection {collection_id} has ark already, no update needed."
            )
            return
        import ark_client

        if not location:
            base_url = (
                settings.JAMA_SITE[:-1]
                if settings.JAMA_SITE[-1] == "/"
                else settings.JAMA_SITE
            )
            location = base_url + reverse(
                "ark_collection", kwargs={"collection_id": collection_id}
            )
        client = ark_client.Client(
            settings.ARK_APP_ID, settings.ARK_SECRET_KEY, settings.ARK_SERVER
        )
        if collection.ark:
            client.update(collection.ark, location)
        else:
            ark_name = client.create(location)
            collection.ark = ark_name
            Collection.objects.filter(pk=collection.pk).update(ark=ark_name)


@db_task()
def recursive_set_metas_to_collection(
    user_id: int, collection_id: int, metas: List[dict], user_task_id: int = None
) -> bool:
    r"""
    Sets all metas for a unique metadata set.

    Metas is a list of metadata id => metadata value dictionaries.

    All metas must share the same metadata set.

    the meta will be set to all direct children resources.

    /!\ *Not* actually recursive: Descendants (sub-collections and sub-collections resources) are IGNORED.
    """
    from rpc.methods import (
        remove_meta_value_from_collection,
        add_meta_to_collection,
        set_metas_to_resource,
    )
    from resources.models import Metadata, Collection, MetadataSet, UserTask
    from django.contrib.auth.models import User

    user_task = UserTask.objects.filter(pk=user_task_id).first()
    if user_task:
        user_task.started_at = timezone.now()
        user_task.save()

    # prevent mixing metas from different sets
    metadatasets_ids = []
    for meta_dict in metas:
        meta = Metadata.objects.get(pk=meta_dict["id"])
        metadatasets_ids.append(meta.set.pk)
    metadatasets_ids = list(set(metadatasets_ids))
    if len(metadatasets_ids) > 1:
        if user_task:
            user_task.failed_at = timezone.now()
            user_task.save()
        return False

    # check that objects exist
    collection_instance = Collection.objects.filter(
        pk=collection_id, deleted_at__isnull=True
    ).first()
    if not collection_instance:
        if user_task:
            user_task.failed_at = timezone.now()
            user_task.save()
        return False
    metadataset_instance = MetadataSet.objects.filter(pk=metadatasets_ids[0]).first()
    if not metadataset_instance:
        if user_task:
            user_task.failed_at = timezone.now()
            user_task.save()
        return False

    user = User.objects.filter(pk=user_id).first()
    if not user:
        if user_task:
            user_task.failed_at = timezone.now()
            user_task.save()
        return False

    # remove all metas from the set
    for meta_value in collection_instance.metadatacollectionvalue_set.filter(
        metadata__set=metadataset_instance
    ):
        remove_meta_value_from_collection(user, collection_id, meta_value.pk)

    # add metas
    for meta_dict in metas:
        add_meta_to_collection(user, collection_id, meta_dict["id"], meta_dict["value"])

    for resource in collection_instance.resources.filter(deleted_at__isnull=True):
        set_metas_to_resource(user, resource.pk, metas)

    if user_task:
        user_task.finished_at = timezone.now()
        user_task.save()
    return True


@db_task()
def update_data_from_xlsx_rows(
    user_id: int, xlsx_rows: List[dict], user_task_id: int = None
):
    from django.contrib.auth.models import User
    from resources.models import UserTask

    project = None

    # Try to find the project
    for r in xlsx_rows:
        if r.get("resource_pk"):
            first_resource = models.Resource.objects.filter(
                pk=r.get("resource_pk")
            ).first()
            if first_resource:
                project = first_resource.ptr_project
                break
        if r.get("collection_pk"):
            first_collection = models.Collection.objects.filter(
                pk=r.get("collection_pk")
            ).first()
            if first_collection:
                project = first_collection.project
                break
    user_task = None
    user = User.objects.filter(pk=user_id).first()
    if user:
        if user_task_id is not None:
            user_task = UserTask.objects.filter(pk=user_task_id).first()
            if user_task:
                user_task.project = project
                user_task.started_at = timezone.now()
                user_task.save()
        from rpc.methods import (
            update_resource_from_xlsx_row,
            update_collection_from_xlsx_row,
            ServiceException,
        )

        for xlsx_row in xlsx_rows:
            try:
                if xlsx_row.get("resource_pk"):
                    update_resource_from_xlsx_row(user, xlsx_row)
                if xlsx_row.get("collection_pk"):
                    update_collection_from_xlsx_row(user, xlsx_row)
            except ServiceException as e:
                logger.warning(e)
        if user_task:
            user_task.finished_at = timezone.now()
            user_task.save()


@db_periodic_task(crontab(hour="*/6"))
def ensureiiif():
    from resources.models import File
    from resources.helpers import iiif_destination_dir_from_hash

    start_date = timezone.now() - timezone.timedelta(days=1)
    for f in (
        File.objects.filter(
            file_type__serve_with_iiif=True,
            deleted_at__isnull=True,
            created_at__gte=start_date,
            tiled=False,
        )
        .distinct()
        .iterator()
    ):
        iiif_destination_dir = iiif_destination_dir_from_hash(f.hash)
        iiif_destination_file = "{}{}".format(iiif_destination_dir, f.hash)
        if not os.path.exists(iiif_destination_file):
            iiif_task(f.pk)
            logger.info(f"tasked missing IIIF for file({f.pk})")


@db_periodic_task(crontab(hour="*/6"))
def clean_partial_uploads():
    now = time.time()
    max_age = 60 * 60 * 6
    sub_folders = [
        f.path for f in os.scandir(settings.PARTIAL_UPLOADS_DIR) if f.is_dir()
    ]
    for folder in sub_folders:
        folder_time = os.path.getmtime(folder)
        if now - folder_time > max_age:
            logger.info(f"removing partial uploads dir {folder}")
            shutil.rmtree(folder)


@db_periodic_task(crontab(hour="*/6"))
def denorm_sizes():
    from resources.models import File

    start_date = timezone.now() - timezone.timedelta(days=1)
    for file in (
        File.objects.filter(
            denormalized_image_height__isnull=True,
            denormalized_image_width__isnull=True,
            file_type__serve_with_iiif=True,
            deleted_at__isnull=True,
            created_at__gte=start_date,
        )
        .distinct()
        .iterator()
    ):
        try:
            x = file.image_width()
            y = file.image_height()
            if x and y:
                file.save()
                logger.info(f"denormed sizes({x},{y}) for file({file.id})")
            else:
                logger.warning(f"can't find x and y for {file.pk}")
        except UnidentifiedImageError:
            logger.warning(f"can't identify {file.pk}")
        except DecompressionBombError:
            logger.warning(f"can't decompress {file.pk}")


@db_periodic_task(crontab(day="1"))
def check_files_integrity():
    def file_hash256(file_path: str) -> str:
        try:
            hsh = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chnk in iter(lambda: f.read(8192), b""):
                    hsh.update(chnk)
            return hsh.hexdigest()
        except FileNotFoundError:
            return ""

    cursor = connection.cursor()
    cursor.execute(
        "select distinct(hash) from resources_file where resources_file.integrity_check_failed_at is null"
    )
    for row in cursor.fetchall():
        new_hash = file_hash256(models.hash_to_local_path(row[0]))
        if new_hash != row[0]:
            logger.warning(f"FILE INTEGRITY CHECK FAILED. File hash: {row[0]}")
            models.File.objects.filter(hash=row[0]).update(
                integrity_check_failed_at=timezone.now()
            )
    connection.close()
