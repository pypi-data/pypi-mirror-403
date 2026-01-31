import os
import json
import glob
import shutil
import tempfile
import validators

from alive_progress import alive_bar
from PIL import Image

from .utils import verify_filename, crop_image, rotate_image


class DatasetFile:
    def __init__(self, data_type, filepath: str, tags: list = [], related_files: list = [], extra: dict = {}) -> None:
        self.filepath = verify_resources([filepath], False, data_type)[0]
        self.tags = tags if len(tags) > 0 else None
        self.related_files = related_files if len(related_files) > 0 else None
        self.extra = extra if len(extra.keys()) > 0 else None


def verify_resources(resources, recursive, category):
    files = []
    if category == "video":
        if isinstance(resources, (list, tuple)):
            if len(resources) != 1:
                raise Exception("Upload a single video file")
            else:
                resource = resources[0]
        elif type(resources) == str:
            resource = resources
        else:
            raise Exception("Invalid video file")

        if not resource.endswith(".mp4"):
            raise Exception("Video format not supported")
        return [verify_filename(resource)]

    if not isinstance(resources, (list, tuple)):
        raise TypeError('resouces type should be a list/tuple')

    def _verify_single_file(file):
        temp = glob.glob(verify_filename(resource))
        if not temp:
            raise FileNotFoundError(file)

    for resource in resources:
        resource = os.path.abspath(resource)
        if recursive == True:
            if os.path.isdir(resource):
                files.extend([verify_filename(y) for x in os.walk(resource)
                              for y in glob.glob(os.path.join(x[0], '*.png'))
                              + glob.glob(os.path.join(x[0], '*.jpg'))
                              + glob.glob(os.path.join(x[0], '*.jpeg'))
                              + glob.glob(os.path.join(x[0], '*.tiff'))
                              ])

            else:
                _verify_single_file(resource)
                files.append(resource)
        else:
            if os.path.isdir(resource):
                files.extend([verify_filename(os.path.join(resource, i)) for i in os.listdir(
                    resource) if i.endswith(('.jpg', '.png', '.jpeg', '.tiff'))])

            else:
                _verify_single_file(resource)
                files.append(resource)

    return files


def image_transformations(save_files_dir, imagepath, keys, crop, rotate):
    extension = os.path.splitext(imagepath)[1]
    if extension not in ('.jpg', '.png', '.jpeg'):
        raise Exception(f"'{extension}' files are not supported")

    valid_transformations = {"crop", "rotate"}
    crop_rotate_func_mapping = {
        "crop": crop_image,
        "rotate": rotate_image
    }

    if len(keys) == 1:
        return imagepath

    if len(keys) == 2:
        transformation = keys[1]
        if transformation not in valid_transformations:
            raise Exception(f"Invalid Image Transformation '{transformation}'")
        img = Image.open(imagepath)
        imageobject = crop_rotate_func_mapping[transformation](
            imagepath, img, crop, rotate
        )

    elif len(keys) == 3:
        # crop/rotate in same order as mentioned in manifest file

        t1, t2 = keys[1], keys[2]
        if not {t1, t2} == valid_transformations:
            raise Exception("Invalid Image Transformations for a folder")
        img = Image.open(imagepath)

        imageobject = crop_rotate_func_mapping[t1](
            imagepath, img, crop, rotate
        )
        imageobject = crop_rotate_func_mapping[t2](
            imagepath, imageobject, crop, rotate
        )

    new_imagepath = os.path.join(save_files_dir, os.path.basename(imagepath))
    imageobject.save(new_imagepath)

    return new_imagepath


def verify_manifest(manifest, save_files_dir, dataset_id, category):

    if save_files_dir and not os.path.exists(save_files_dir):
        raise Exception(f"directory {save_files_dir} not found")
    save_files_dir_temp = tempfile.mkdtemp(prefix=f'dataset_id_{dataset_id}_')
    manifest = os.path.abspath(manifest)
    files = []
    if category.lower() != 'image':
        raise Exception("Invalid dataset category for manifest file")
    try:
        f = open(manifest)
        data = json.load(f)
    except:
        raise Exception(f"Invalid manifest file '{manifest}'")
    if ("images" not in data) and ("folders" not in data):
        raise Exception(
            f"'couldn't find 'images or/and folders' in '{manifest}'")

    if "images" in data:
        images = data["images"]
        with alive_bar(len(images), dual_line=True, title=f'\033[1m Files \033[0m') as bar:
            for image in images:

                keys = list(image.keys())

                if len(keys) not in (1, 2, 3) or keys[0] != "path":
                    raise Exception("invalid manifest file format")
                imagepath = verify_filename(image["path"])
                bar.text = f'-> cropping/rotating the image: {imagepath}'
                crop = image["crop"] if "crop" in image else None
                rotate = image["rotate"] if "rotate" in image else None

                transformed_file = image_transformations(
                    save_files_dir_temp,
                    imagepath,
                    keys,
                    crop,
                    rotate
                )
                files.append(transformed_file)

                bar()
    print("\n")

    if "folders" in data:
        for folder in data["folders"]:
            keys = list(folder.keys())
            if keys[0] != "path" or len(keys) not in (1, 2, 3):
                raise Exception(f"invalid manifest file folder")
            resource = folder["path"]

            basename = os.path.basename(os.path.normpath(resource))
            new_save_files_dir = os.path.join(save_files_dir_temp, basename)
            if not os.path.exists(new_save_files_dir):
                os.makedirs(new_save_files_dir)

            images = []
            images.extend([verify_filename(os.path.join(resource, i)) for i in os.listdir(resource)
                           if i.endswith(('.jpg', '.png', '.jpeg'))])
            crop = folder["crop"] if "crop" in folder else None
            rotate = folder["rotate"] if "rotate" in folder else None

            with alive_bar(len(images), dual_line=True, title=f'\033[1m {resource}\033[0m') as bar:
                for imagepath in images:
                    bar.text = f'-> cropping/rotating the image: {imagepath}'

                    transformed_file = image_transformations(
                        new_save_files_dir,
                        imagepath,
                        keys,
                        crop,
                        rotate
                    )
                    files.append(transformed_file)

                    bar()

            print("\n")
    if save_files_dir:
        shutil.move(save_files_dir_temp, save_files_dir)
    return files


def validate_related_file_extra(extra: dict):
    errors = []
    device_id = extra.get('device_id', None)
    if device_id is None or not isinstance(device_id, int) or device_id < 0:
        errors.append('Invalid device_id')

    supported_url = extra.get('supported_file_url', None)
    if supported_url and not validators.url(supported_url):
        errors.append('invalid supported_url')

    if 'cameraModel' in extra and extra['cameraModel'] not in ('PINHOLE', 'FISHEYE'):
        errors.append('Invalid choice for cameraModel')
    if 'mirror' in extra and not isinstance(extra['mirror'], int):
        errors.append('Invalid mirror value')

    intrinsic = extra.get('intrinsic', None)
    if intrinsic:
        if not isinstance(intrinsic,list) or (len(intrinsic)!=4 or not all(isinstance(item, (int,float)) for item in intrinsic)):
            errors.append('Invalid intrinsic values')

    distortion = extra.get('distortion', None)
    if distortion:
        if not isinstance(distortion,list) or (len(distortion)>10 or not all(isinstance(item, (int,float)) for item in distortion)):
            errors.append('Invalid distortion values')

    extrinsic = extra.get('extrinsic', None)
    if extrinsic:
        if not isinstance(extrinsic,list) or (len(extrinsic)!=4 or not all(len(grid)==4 and all(isinstance(item, (int,float)) \
                                                    for item in grid) for grid in extrinsic)):
            errors.append('Invalid extrinsic values')

    if errors:
        raise Exception(errors)


def validate_user_cloud_manifest_file(manifest_filepath, data_type):
    json_data = json.load(open(manifest_filepath, 'r'))
    if len(json_data) > 10000:
        raise Exception("File too large")
    
    valid_relatedfile_types = ('.jpg', '.jpeg', '.png')
    valid_mainfile_types = ('.pcd',) if data_type=='pointcloud' else valid_relatedfile_types if data_type=='image' else ()
    sequence_list = []
    for item in json_data:
        try:
            mainfile = item['mainfile']
        except KeyError:
            raise Exception("each item requires a mainfile")
        if not mainfile.endswith(valid_mainfile_types):
            raise Exception(f"Invalid file extension for mainfile {mainfile}. Supported file extensions are: {valid_mainfile_types}")
        
        sequence = item.get('sequence', None)
        if sequence is not None and (not isinstance(sequence, int) or sequence < 1):
            raise Exception("Sequence should be a positive integer")
        sequence_list.append(sequence)

        tags = item.get('tags', [])
        if not isinstance(tags, (list, tuple)) or len(tags) > 10:
            raise Exception(f"Invalid tags list for mainfile {mainfile}")
        
        ref_images = item.get('ref_images', [])
        for ref_img in ref_images:
            try:
                filepath = ref_img['filepath']
            except KeyError:
                raise Exception("each ref_image requires a filepath")
            if not filepath.endswith(valid_relatedfile_types):
                raise Exception(f"Invalid file extension for ref_image {filepath}")
            
            tags = ref_img.get('tags', [])
            if not isinstance(tags, (list, tuple)) or len(tags) > 10:
                raise Exception(f"Invalid tags list for ref_image {filepath}")
            
            validate_related_file_extra(ref_img['camera_params'])

    if len(sequence_list) != len(set(sequence_list)):
        raise Exception("Duplicate sequence value found")