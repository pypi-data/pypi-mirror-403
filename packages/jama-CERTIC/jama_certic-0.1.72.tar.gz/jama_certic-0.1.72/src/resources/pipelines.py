from typing import Dict, Union
from .models import Resource, Collection, File

import logging

logger = logging.getLogger(__name__)

# Pipelines are simple functions taking resources or collections and params.
# Pipelines functions can be added in Jama apps in module pipelines.py
# Each pipeline is executed every time a resource or a collection is saved.
# Each pipeline has to determine itelf if it's up to the task (example:
# object is not a Resource, I return) and has to take care of the conditions of
# execution (example: start an async task or not).
# Order of execution is not guaranteed and no return is expected.
# This is basically per-project pluggable signals for Resources and Collections.

# /!\ Since pipelines are executed upon Resource, File and Collection post-save event,
# pipelines and subsequent code should never call Resource, File or Collection save(), at
# the risk of creating a loop.
# Use QuerySet update() if you need to update a row, don't use the model's save() method.


def make_iiif(obj: Union[Resource, File, Collection], parameters: Dict = None):
    if type(obj) is Collection:
        return
    if obj.file and obj.file.should_have_iiif:
        from resources.tasks import iiif_task

        iiif_task(obj.file.pk)


def make_hls(obj: Union[Resource, File, Collection], parameters: Dict = None):
    if type(obj) is Collection:
        return
    if obj.file and obj.file.should_have_hls:
        from resources.tasks import hls_task

        hls_task(obj.file.pk)


def tesseract_ocr(obj: Union[Resource, File, Collection], parameters: Dict = None):
    if type(obj) is Collection:
        return
    if obj.file and obj.file.should_have_iiif:
        from resources.tasks import ocr_task

        ocr_task(obj.file.pk)


def exiftool(obj: Union[Resource, File, Collection], parameters: Dict = None):
    if type(obj) is Collection:
        return
    if obj.file:
        from resources.tasks import exif_task

        exif_task(obj.file.pk)


def arkify(obj: Union[Resource, File, Collection], parameters):
    from resources.tasks import set_ark_to_collection, set_ark_to_resource

    if type(obj) is Collection:
        set_ark_to_collection(obj.pk)
    if type(obj) in [Resource, File]:
        set_ark_to_resource(obj.pk)
