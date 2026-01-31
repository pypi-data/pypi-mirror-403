import io
import re
import os

def convert_image_to_bytes(
    imagepath,
    imageobject,
    extension
):
    try:
        buf = io.BytesIO()
        extensions = {'.png': 'PNG', '.jpeg': 'JPEG', '.jpg': 'JPEG'}
        imageobject.save(
            buf,
            format=extensions[extension],
            quality='keep'
        )
        byte_im = buf.getvalue()
        file_size = buf.tell()
    except Exception as e:
        print(f"could not convert '{imagepath}' to .png")
        raise e

    return byte_im, file_size


def verify_filename(filename):
    allowed = r'^[a-zA-Z0-9_ +!\-_*\'().]+$'
    if re.match(allowed, os.path.basename(filename)) is None:
        raise Exception(f"Invalid Filename : {filename}")
    
    return filename


def crop_image(
    imagepath,
    img,
    crop,
    rotate
):
    # Crop format : Number of pixels you want to remove from (left, top, right, bottom)
    w, h = img.size
    if all(isinstance(x, int) for x in crop) == False:
        raise Exception(f"could not crop '{imagepath}'. invalid crop entries")

    cropped_img = img.crop((crop[0], crop[1], w-crop[2], h-crop[3]))
    return cropped_img


def rotate_image(
    imagepath,
    img,
    crop,
    rotate
):
    if rotate not in (90, 180, 270):
        raise Exception(
            f"Could not rotate image '{imagepath}'. Rotate angle should be 90,180 or 270 (clockwise)")

    rotated_img = img.rotate(rotate)
    return rotated_img