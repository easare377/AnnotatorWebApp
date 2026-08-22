"""Local image converter with the same payload shape as the future Lambda."""

import io
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError

from ..controller import Controller, ok
from ..decorators.route import route


DEFAULT_MAX_SOURCE_BYTES = 100 * 1024 * 1024
REMOTE_REQUEST_TIMEOUT_SECONDS = 30
RESAMPLE_FILTER = (
    Image.Resampling.LANCZOS
    if hasattr(Image, "Resampling")
    else Image.LANCZOS
)
OUTPUT_FORMATS = {
    "png": ("PNG", "image/png"),
    "jpg": ("JPEG", "image/jpeg"),
    "jpeg": ("JPEG", "image/jpeg"),
}


def local_upload_path(url: str) -> Path | None:
    """Resolve a local upload URL to a safe path below ``BASE_DIR/uploads``."""
    parsed_url = urlparse(str(url))
    decoded_path = unquote(parsed_url.path)
    relative_path = None

    for prefix in ("/api/uploads/", "/uploads/"):
        if decoded_path.startswith(prefix):
            relative_path = decoded_path[len(prefix) :]
            break

    if relative_path is None:
        return None

    upload_root = (Path(settings.BASE_DIR) / "uploads").resolve()
    resolved_path = (upload_root / relative_path).resolve()
    try:
        resolved_path.relative_to(upload_root)
    except ValueError:
        raise ValueError("The upload URL points outside the uploads directory.")
    return resolved_path


def read_source_bytes(original_url: str) -> bytes:
    """Read an original image from local storage or an HTTP(S) URL."""
    local_path = local_upload_path(original_url)
    max_source_bytes = getattr(
        settings,
        "LOCAL_CONVERTER_MAX_SOURCE_BYTES",
        DEFAULT_MAX_SOURCE_BYTES,
    )

    if local_path is not None:
        if not local_path.is_file():
            raise ValueError("The original image does not exist.")
        if local_path.stat().st_size > max_source_bytes:
            raise ValueError("The original image exceeds the converter size limit.")
        return local_path.read_bytes()

    parsed_url = urlparse(str(original_url))
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("originalUrl must be a local upload or HTTP(S) URL.")

    try:
        with requests.get(
            original_url,
            stream=True,
            timeout=REMOTE_REQUEST_TIMEOUT_SECONDS,
        ) as response:
            response.raise_for_status()
            source = io.BytesIO()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                source.write(chunk)
                if source.tell() > max_source_bytes:
                    raise ValueError(
                        "The original image exceeds the converter size limit."
                    )
            return source.getvalue()
    except requests.RequestException as error:
        raise ValueError(f"Failed to download the original image: {error}")


def parse_size(size) -> tuple[int, int] | None:
    """Return a width/height bound, or None to preserve the original size."""
    if size is None:
        return None

    if isinstance(size, (list, tuple)) and len(size) == 2:
        width, height = size
    elif isinstance(size, dict):
        width, height = size.get("width"), size.get("height")
    else:
        width = getattr(size, "width", None)
        height = getattr(size, "height", None)

    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or width <= 0
        or height <= 0
    ):
        raise ValueError("size must contain positive integer width and height values.")
    return width, height


def flatten_for_jpeg(image: Image.Image) -> Image.Image:
    """Convert an image to RGB, compositing transparency onto white."""
    if image.mode == "RGB":
        return image.copy()
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba_image = image.convert("RGBA")
        background = Image.new("RGB", rgba_image.size, (255, 255, 255))
        background.paste(rgba_image, mask=rgba_image.getchannel("A"))
        return background
    return image.convert("RGB")


def prepare_output_image(image: Image.Image, extension: str) -> Image.Image:
    """Return an image mode suitable for the requested output extension."""
    if extension in ("jpg", "jpeg"):
        return flatten_for_jpeg(image)
    if image.mode in ("RGB", "RGBA"):
        return image.copy()
    if "A" in image.getbands() or image.mode == "P":
        return image.convert("RGBA")
    return image.convert("RGB")


def encode_output_image(
    source_image: Image.Image,
    extension: str,
    size,
) -> tuple[bytes, tuple[int, int]]:
    """Resize and encode one output from an already decoded source image."""
    normalized_extension = str(extension).lower().lstrip(".")
    if normalized_extension not in OUTPUT_FORMATS:
        raise ValueError("ext must be png, jpg, or jpeg.")

    image = source_image.copy()
    requested_size = parse_size(size)
    if requested_size is not None:
        image.thumbnail(requested_size, RESAMPLE_FILTER)

    output_image = prepare_output_image(image, normalized_extension)
    output = io.BytesIO()
    image_format, _ = OUTPUT_FORMATS[normalized_extension]
    save_options = (
        {"compress_level": 9}
        if image_format == "PNG"
        else {"quality": 85}
    )
    output_image.save(output, format=image_format, **save_options)
    return output.getvalue(), output_image.size


def write_output_bytes(output_url: str, output_bytes: bytes, content_type: str) -> None:
    """Write converted bytes locally or PUT them to a presigned HTTP(S) URL."""
    local_path = local_upload_path(output_url)
    if local_path is not None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=local_path.parent,
                prefix=f".{local_path.name}.",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(output_bytes)
            temporary_path.replace(local_path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return

    parsed_url = urlparse(str(output_url))
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("outputUrl must be a local upload or HTTP(S) URL.")
    try:
        response = requests.put(
            output_url,
            data=output_bytes,
            headers={"Content-Type": content_type},
            timeout=REMOTE_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise ValueError(f"Failed to write the converted image: {error}")


def output_value(output, field_name: str, default=None):
    """Read a conversion-output field from a dict or request object."""
    if isinstance(output, dict):
        return output.get(field_name, default)
    return getattr(output, field_name, default)


def remove_local_outputs(output_urls) -> None:
    """Best-effort cleanup for outputs written before a batch failure."""
    for output_url in output_urls:
        output_path = local_upload_path(output_url)
        if output_path is not None:
            output_path.unlink(missing_ok=True)


def convert_image_outputs(original_url: str, outputs) -> dict:
    """Download and decode one original, then generate every requested output."""
    if not isinstance(outputs, (list, tuple)) or not outputs:
        raise ValueError("outputs must contain at least one conversion target.")

    source_bytes = read_source_bytes(original_url)
    written_output_urls = []
    conversion_results = []

    try:
        with Image.open(io.BytesIO(source_bytes)) as opened_image:
            source_image = ImageOps.exif_transpose(opened_image)
            source_image.load()

            for output in outputs:
                upload_id = output_value(output, "upload_id")
                output_url = output_value(output, "output_url")
                extension = output_value(output, "ext")
                size = output_value(output, "size")

                if not upload_id:
                    raise ValueError("Each output requires uploadId.")
                if not output_url:
                    raise ValueError("Each output requires outputUrl.")

                normalized_extension = str(extension).lower().lstrip(".")
                if normalized_extension not in OUTPUT_FORMATS:
                    raise ValueError("ext must be png, jpg, or jpeg.")

                output_bytes, output_size = encode_output_image(
                    source_image,
                    normalized_extension,
                    size,
                )
                _, content_type = OUTPUT_FORMATS[normalized_extension]
                write_output_bytes(output_url, output_bytes, content_type)
                written_output_urls.append(output_url)
                conversion_results.append(
                    {
                        "uploadId": str(upload_id),
                        "outputUrl": output_url,
                        "ext": normalized_extension,
                        "width": output_size[0],
                        "height": output_size[1],
                    }
                )
    except UnidentifiedImageError:
        remove_local_outputs(written_output_urls)
        raise ValueError("The original URL does not contain a readable image.")
    except Exception:
        remove_local_outputs(written_output_urls)
        raise

    return {
        "originalUrl": original_url,
        "outputs": conversion_results,
    }


@route("projects/data/convert-image")
class ConvertImageController(Controller):
    """Convert one ``originalUrl`` into every entry in ``outputs``.

    Each output contains ``uploadId``, ``outputUrl``, ``ext``, and ``size``.
    ``size`` may be null to preserve the source dimensions or an object such
    as ``{"width": 320, "height": 320}`` to constrain that output.
    """

    def process_post_request(self, request_object):
        conversion_result = convert_image_outputs(
            request_object.original_url,
            request_object.outputs,
        )
        return ok(conversion_result)
