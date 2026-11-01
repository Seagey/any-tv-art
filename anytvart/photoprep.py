"""Getting a phone photo of the room ready for the AI to look at, privately.

Phone photos carry the place they were taken (GPS) and the camera's details. This strips all of
that by drawing the pixels into a fresh image, shrinks it (the check needs shapes, not detail),
and saves it in data/, which git ignores. The original is never changed.
"""
import os

from PIL import Image, ImageOps

LONG_EDGE = 1600


def prep(src, out_dir, crop=None):
    """crop: (left, top, right, bottom) as fractions, to keep only the TV and the paper."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if crop:
            l, t, r, b = crop
            im = im.crop((int(l * im.width), int(t * im.height), int(r * im.width), int(b * im.height)))
        im.thumbnail((LONG_EDGE, LONG_EDGE), Image.LANCZOS)
        clean = Image.new("RGB", im.size)
        clean.paste(im)          # pixels only: no EXIF, no GPS, no maker notes, no ICC profile
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "check-" + os.path.splitext(os.path.basename(src))[0] + ".jpg")
    clean.save(out, "JPEG", quality=88)
    return out


def has_location(path):
    """True if the photo still carries GPS. Used by the tests and by `anytvart photo-prep --check`."""
    with Image.open(path) as im:
        exif = im.getexif()
        return bool(exif.get_ifd(0x8825)) if exif else False
