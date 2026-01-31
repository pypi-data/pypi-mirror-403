import shutil
import exiftool
import hashlib
from django.core.files.base import File
from jama import settings
from resources import models
import re
import os
import unicodedata
from shutil import copyfile
from subprocess import call
from django.db.utils import IntegrityError
from unidecode import unidecode
import logging
from typing import Union
from pathlib import Path
import subprocess

logger = logging.getLogger(__name__)


def _file_hash256(file_path: str) -> str:
    hsh = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chnk in iter(lambda: f.read(8192), b""):
            hsh.update(chnk)
    return hsh.hexdigest()


def _try_to_remove(file_path: Union[str, Path]) -> bool:
    try:
        os.remove(file_path)
        return True
    except FileNotFoundError:
        return False


def pic_to_tiled_tiff(
    source: Union[str, Path], destination: Union[str, Path], dpi: int = 300
) -> int:
    tif_source = "{}.delme.tif".format(source)
    _, extension = os.path.splitext(source)
    if extension.lower() in {".pdf", ".ai"}:
        pdftoppm_dest = "{}.delme".format(
            source
        )  # pdftoppm adds .tif extension already...
        status = call(
            [
                "pdftoppm",
                "-singlefile",
                "-tiff",
                source,
                "-r",
                str(dpi),
                pdftoppm_dest,
            ]
        )
    else:
        status = call(
            [
                "convert",
                source,
                "-set",
                "colorspace:auto-grayscale",
                "false",
                "-auto-orient",
                "-colorspace",
                "sRGB",
                "-depth",
                "8",
                tif_source,
            ]
        )
    if status != 0:
        logger.warning(f"failed convert {source}")
        _try_to_remove(tif_source)
        return status
    tile_command = [
        "vips",
        "im_vips2tiff",
        tif_source,
        "{}:deflate,tile:256x256,pyramid".format(destination),
    ]
    if settings.JAMA_USE_WEBP:
        tile_command = [
            "vips",
            "tiffsave",
            tif_source,
            destination,
            "--tile",
            "--pyramid",
            "--tile-width",
            "256",
            "--tile-height",
            "256",
            "--Q",
            "90",
            "--compression",
            "webp",
        ]
    status = call(tile_command)
    if status != 0:
        logger.warning(f"failed tiling {tif_source}")
        logger.warning(" ".join([str(x) for x in tile_command]))
        _try_to_remove(destination)
    _try_to_remove(tif_source)
    return status


class ResourceError(RuntimeError):
    pass


def file_metadatas(file_path: str) -> dict:
    with exiftool.ExifToolHelper() as et:
        datas = et.get_metadata([file_path])
        return datas[0]


def hash_upload(f: File) -> str:
    file_hash = hashlib.sha256()
    for chunk in f.chunks():
        file_hash.update(chunk)
    return file_hash.hexdigest()


class UnknownFileType(RuntimeError):
    pass


class ConcurrencyError(RuntimeError):
    pass


def get_file_type_from_extension(extension: str) -> models.FileType:
    extension = extension.lower()[1:]
    file_type = models.FileType.objects.filter(extensions__label=extension).first()
    if not file_type:
        raise UnknownFileType("Type de fichier inconnu")
    return file_type


def make_ocr(f: Union[models.File, int], refresh: bool = False):
    """
    Performs OCR on file if OCR output not yet available.
    Use refresh = True to force OCR.
    """
    if type(f) is int:
        f = models.File.objects.get(pk=f)
    f.make_ocr(refresh)


def iiif_destination_dir_from_hash(hash: str) -> str:
    return "{}{}{}{}{}{}".format(
        settings.IIIF_DIR,
        os.path.sep,
        hash[:2],
        os.path.sep,
        hash[2:4],
        os.path.sep,
    )


def hls_destination_dir_from_hash(hash: str) -> str:
    return "{}{}{}{}{}{}{}{}".format(
        settings.HLS_DIR,
        os.path.sep,
        hash[:2],
        os.path.sep,
        hash[2:4],
        os.path.sep,
        hash,
        os.path.sep,
    )


def make_hls(f: Union[models.File, int], force: bool = False):
    """
    Convert a video to HLS format

    Will silently return if not a video format
    or if conversion already exists, except if force is True.
    """

    if type(f) is int:
        f = models.File.objects.get(pk=f)
    if f.should_have_hls:
        hls_destination_dir = hls_destination_dir_from_hash(f.hash)
        if force or not os.path.exists(hls_destination_dir):
            os.makedirs(hls_destination_dir, exist_ok=True)
            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                f.local_path(),
                "-filter_complex",
                (
                    "[0:v]split=3[v1][v2][v3];"
                    "[v1]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[v1out];"
                    "[v2]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black[v2out];"
                    "[v3]scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2:black[v3out]"
                ),
                # Video streams
                # video 1
                "-map",
                "[v1out]",
                "-c:v:0",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-b:v:0",
                "5000k",
                "-maxrate:v:0",
                "5350k",
                "-bufsize:v:0",
                "7500k",
                # video 2
                "-map",
                "[v2out]",
                "-c:v:1",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-b:v:1",
                "2800k",
                "-maxrate:v:1",
                "2996k",
                "-bufsize:v:1",
                "4200k",
                # video 3
                "-map",
                "[v3out]",
                "-c:v:2",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-b:v:2",
                "1400k",
                "-maxrate:v:2",
                "1498k",
                "-bufsize:v:2",
                "2100k",
                # Audio streams
                # audio 1
                "-map",
                "a:0",
                "-c:a:0",
                "aac",
                "-b:a:0",
                "192k",
                "-ac",
                "2",
                # audio 2
                "-map",
                "a:0",
                "-c:a:1",
                "aac",
                "-b:a:1",
                "128k",
                "-ac",
                "2",
                # audio 3
                "-map",
                "a:0",
                "-c:a:2",
                "aac",
                "-b:a:2",
                "96k",
                "-ac",
                "2",
                # HLS settings
                "-f",
                "hls",
                "-hls_time",
                "3",
                "-hls_playlist_type",
                "vod",
                "-hls_flags",
                "independent_segments",
                "-hls_segment_type",
                "mpegts",
                "-hls_segment_filename",
                f"{hls_destination_dir}stream_%v{os.path.sep}data%03d.ts",
                "-master_pl_name",
                "master.m3u8",
                "-var_stream_map",
                "v:0,a:0 v:1,a:1 v:2,a:2",
                # playlist output
                f"{hls_destination_dir}stream_%v{os.path.sep}playlist.m3u8",
            ]

            subprocess.run(ffmpeg_cmd, check=True)


def make_iiif(f: Union[models.File, int], force: bool = False):
    """
    Make a Tiled TIF ready for IIIF server.

    Will silently return if not a image format
    or if tiled TIF already exists, except if force is True.
    """
    if type(f) is int:
        f = models.File.objects.get(pk=f)
    if f.should_have_iiif:
        iiif_destination_dir = iiif_destination_dir_from_hash(f.hash)
        iiif_destination_file = "{}{}".format(iiif_destination_dir, f.hash)
        if not os.path.isfile(iiif_destination_file) or force:
            if force:
                logger.debug(f"forcing IIIF tiling of File({f.pk})")
            _, extension = os.path.splitext(f.original_name)
            tmp_source_file = Path(
                settings.JAMA_IIIF_PROCESSING_DIR, f.hash + extension
            )
            os.makedirs(settings.JAMA_IIIF_PROCESSING_DIR, exist_ok=True)
            copyfile(f.local_path(), tmp_source_file)  # Source may be on slow volume
            tmp_iiif_file = Path(
                settings.JAMA_IIIF_PROCESSING_DIR, f.hash + ".tiled" + extension
            )
            status = pic_to_tiled_tiff(tmp_source_file, tmp_iiif_file)
            if status != 0:
                logger.error(
                    "IIIF conversion of file({}) stopped with status {}".format(
                        f.pk, status
                    )
                )
                _try_to_remove(tmp_source_file)
                _try_to_remove(tmp_iiif_file)
                return
            os.makedirs(iiif_destination_dir, exist_ok=True, mode=0o775)
            shutil.copyfile(tmp_iiif_file, iiif_destination_file)
            _try_to_remove(tmp_source_file)
            _try_to_remove(tmp_iiif_file)
        call(
            [
                "chmod",
                "775",
                "{}{}{}".format(
                    settings.IIIF_DIR,
                    os.path.sep,
                    f.hash[:2],
                ),
            ]
        )
        call(
            [
                "chmod",
                "775",
                iiif_destination_dir,
            ]
        )
        call(["chmod", "775", iiif_destination_file])
        f.tiled = True
        models.File.objects.filter(pk=f.pk).update(tiled=True)


def delete_exif_metas(f: models.File) -> int:
    deleted_counter = 0
    exiftools_metas_set = models.MetadataSet.objects.filter(
        title="ExifTool", project=f.project
    ).first()
    for meta_value in models.MetadataResourceValue.objects.filter(
        resource=f, metadata__set=exiftools_metas_set
    ):
        meta_value.delete()
        deleted_counter = deleted_counter + 1
    return deleted_counter


def set_exif_metas(f: Union[models.File, int]) -> int:
    """
    Will run Exiftool on given models.File.local_path(), only if project has use_exiftool=True.
    Extracted data is then converted to Metadatas.
    ExifTool MetadataSet and Metadatas always have public_project
    as project.
    """
    if type(f) is int:
        f = models.File.objects.get(pk=f)
    added_counter = 0
    if f.project.use_exiftool:
        exiftools_metas = file_metadatas(f.local_path())
        if "ExifTool:Error" not in exiftools_metas:
            # first delete ExifTool metas
            delete_exif_metas(f)
            # then insert new metas from extracted data
            exiftools_metas_set, created = models.MetadataSet.objects.get_or_create(
                title="ExifTool", project=f.project
            )
            for key in exiftools_metas:
                metadata, created = models.Metadata.objects.get_or_create(
                    title=key, set=exiftools_metas_set, project=f.project
                )
                models.MetadataResourceValue.objects.get_or_create(
                    metadata=metadata,
                    value=exiftools_metas[key.strip()],
                    resource=f,
                )
                added_counter = added_counter + 1
    return added_counter


def _copy_uploaded_file_to_destination(
    uploaded_file: File, destination_file: str
) -> bool:
    """
    Store file from the HTTP request locally if it's not here already.

    Returns True if copy, False if not (ie. file already exists).
    False does NOT mean there's an error.
    """
    destination_dir = os.path.dirname(destination_file)
    if not os.path.isfile(destination_file):
        os.makedirs(destination_dir, exist_ok=True)
        with open(destination_file, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        return True
    return False


def handle_local_file(file_path: str, project: models.Project) -> int:
    file_hash = _file_hash256(file_path)
    destination_file = models.hash_to_local_path(file_hash)
    os.makedirs(os.path.dirname(destination_file), exist_ok=True)
    if not os.path.isfile(destination_file):
        shutil.copyfile(file_path, destination_file)
    title, extension = os.path.splitext(os.path.basename(file_path))

    # create db file record if not already here
    file = models.File.objects.filter(hash=file_hash, project=project).first()
    if not file:
        file = models.File.objects.create(
            hash=file_hash,
            title=unidecode(f"{title}{extension}"),
            original_name=unidecode(os.path.basename(file_path)),
            size=os.path.getsize(destination_file),
            project=project,
            file_type_id=get_file_type_from_extension(extension).id,
        )
        file.save()
    if file.deleted_at:
        file.deleted_at = None
        file.save()
    logger.info("Added from local file: {} ({})".format(file.title, file.id))
    return file.id


def handle_uploaded_file(
    uploaded_file: File,
    project: models.Project,
    force_file_name=None,
) -> int:
    upload_hash = hash_upload(uploaded_file)
    destination_file = models.hash_to_local_path(upload_hash)
    _copy_uploaded_file_to_destination(uploaded_file, destination_file)
    title, extension = os.path.splitext(uploaded_file.name)

    # create db file record if not already here
    file = models.File.objects.filter(hash=upload_hash, project=project).first()
    if not file:
        try:
            file = models.File.objects.create(
                hash=upload_hash,
                title=force_file_name or os.path.basename(title),
                original_name=force_file_name or os.path.basename(uploaded_file.name),
                size=uploaded_file.size,
                project=project,
                file_type_id=get_file_type_from_extension(extension).id,
            )
        except IntegrityError:
            raise ConcurrencyError()
    # file is respawned ?
    if file.deleted_at:
        file.deleted_at = None
        if force_file_name:
            file.title = force_file_name
            file.original_name = force_file_name
        file.save()
    return file.id


def slugify_filename(s: str) -> str:
    name, extension = os.path.splitext(s)
    name = name.lower()
    for c in [" ", "-", ".", "/"]:
        name = name.replace(c, "_")
    name = re.sub(r"\W", "", name)
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)
    name = name.strip()
    name = name.replace(" ", "-")
    name = unicodedata.normalize("NFKD", name)
    name = "".join([c for c in name if not unicodedata.combining(c)])

    return name + extension
