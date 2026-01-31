# Copyright (C) 2022 Mindkosh Technologies. All rights reserved.
# Author: Parmeshwar Kumawat

import os
import json
import tempfile
import shutil
import zipfile
from datetime import datetime
import numpy as np

def convert(datasetspath, format, newformat, location):
    try:
        import datumaro
    except ImportError:
        raise Exception("datumaro==0.3.1 is not installed")
    filename = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    annotationfile = os.path.join(location, newformat + "_" + filename)
    tempdir1, tempdir2 = tempfile.mkdtemp(), tempfile.mkdtemp()

    with zipfile.ZipFile(datasetspath, 'r') as zip_ref:
        zip_ref.extractall(tempdir1)

    try:
        dataset = datumaro.Dataset.import_from(tempdir1, format)
        dataset.export(tempdir2, format=newformat, save_images=False)
        shutil.make_archive(annotationfile, 'zip', tempdir2)

    except Exception as e:
        shutil.rmtree(tempdir1)
        shutil.rmtree(tempdir2)
        raise e

    print("Saved : ", annotationfile + ".zip")
    shutil.rmtree(tempdir1)
    shutil.rmtree(tempdir2)


def create(frames, raw_annotations, labels, annotationfile, annotationformat):
    try:
        import datumaro as dm
    except ImportError:
        raise Exception("datumaro==0.3.1 is not installed")
    assert annotationformat in (
        'coco', 'yolo', 'voc', 'datumaro'), f"invalid dataset format : {annotationformat}"

    labels_ = {}
    attributes_ = {}
    categories_ = {}
    categories_idx = 0
    for label in labels:
        labels_[label.id] = label.name
        for attr in label.attributes:
            attributes_[attr.id] = attr.name

    image_id = 1
    dataset_items = []

    for raw_annotation in raw_annotations:

        annotations_ = {}
        shapes = raw_annotation['shapes']
        task_id = raw_annotation['task_id']
        for shape in shapes:
            if not shape['type']:
                annotations_[shape["frame"]] = []
                continue
            points = shape['points']
            attributes = {"occluded": shape["occluded"]}
            for attr in shape['attributes']:
                attributes[attributes_[attr['spec_id']]] = attr['value']

            label_name = labels_[shape['label_id']]
            if label_name not in categories_:
                categories_[label_name] = categories_idx
                label_id = categories_idx
                categories_idx += 1
            else:
                label_id = categories_[label_name]

            if shape['type'] == 'rectangle':
                annotation = dm.Bbox(points[0], points[1], points[2]-points[0], points[3]-points[1],
                                     label=label_id, group=shape['group'],
                                     z_order=shape['z_order'], attributes=attributes)

            elif shape['type'] == 'polygon':
                annotation = dm.Polygon(points, label=label_id,
                                        group=shape['group'], z_order=shape['z_order'], attributes=attributes)

            elif shape['type'] == 'points':
                annotation = dm.Points(points, label=label_id,
                                       group=shape['group'], z_order=shape['z_order'], attributes=attributes)

            elif shape['type'] == 'polyline':
                annotation = dm.PolyLine(points, label=label_id,
                                         group=shape['group'], z_order=shape['z_order'], attributes=attributes)

            elif shape['type'] == 'cuboid':
                continue

            if shape["frame"] in annotations_:
                annotations_[shape["frame"]].append(annotation)
            else:
                annotations_[shape["frame"]] = [annotation]

        for frame_id, frame_obj in frames[task_id].items():
            w, h = frame_obj.width, frame_obj.height
            name, ext = os.path.splitext(frame_obj.name)
            try:
                frame_anno = annotations_[frame_id]
            except KeyError:
                frame_anno = []
            dataset_item = dm.DatasetItem(id=name,
                                          media=dm.components.media.Image(data=np.zeros(
                                              shape=(h, w, 3)), ext=ext),
                                          subset=None,
                                          attributes={'id': image_id},
                                          annotations=frame_anno
                                          )
            dataset_items.append(dataset_item)
            image_id += 1

    dataset = dm.Dataset.from_iterable(
        dataset_items, categories=list(categories_.keys()))

    tempdir = tempfile.mkdtemp()
    dataset.export(tempdir, format=annotationformat, save_images=False)
    try:
        shutil.make_archive(annotationfile, 'zip', tempdir)
    except Exception as e:
        shutil.rmtree(tempdir)
        raise e
    print("Downloaded : ", annotationfile + ".zip")
    shutil.rmtree(tempdir)


def _verify_annotations(file_path,annotation_format,labels):
    if annotation_format=='segmentation_mask':
        raise Exception('format not supported')
    
    label_set = set()
    for label in labels:
        label_set.add(label.name)
        
    tempDir = tempfile.mkdtemp()
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(tempDir)

    if annotation_format == 'mindkosh':
        category_set = validate_mk_datasets(file_path)
    elif annotation_format == 'kitti':
        category_set = validate_kitti_datasets(file_path)
    elif annotation_format == 'cvat':
        return
    else:
        try:
            import datumaro
        except ImportError:
            raise Exception("datumaro==0.3.1 is not installed")
        dataset = datumaro.Dataset.import_from(tempDir, annotation_format)
        categories = dataset.categories()
        category_dict = (next(iter(categories.values()))._indices)
        if annotation_format=='voc':
            category_dict.pop('background',None)
        category_set = set(category_dict.keys())

    if not category_set.issubset(label_set):
        raise Exception(f"""task doesn't have all labels that are present in annotation files.
                task labels : {label_set}
                labels present in annotations : {category_set}"""
                )
    

def validate_mk_datasets(file_path):
    """Returns labels present in datasets
    """
    labels = set()
    supported_anno_types = ['boxes', 'polylines', 'points', 'cuboids', 'polygons', 'tags']
    def get_labels(data):
        meta = data["annotations"]["meta"]
        images = data["annotations"]["images"]

        label_id_name_mapping = {}
        attr_id_name_mapping = {}
        for label in meta["task"]["labels"]:
            label_id_name_mapping[label["id"]] = label["name"]
            for attr in label["attributes"]:
                attr_id_name_mapping[attr["id"]] = attr["name"]

        for image in images:
            for anno_type in supported_anno_types:
                if anno_type in image:
                    for anno in image[anno_type]:
                        label = label_id_name_mapping[anno['label']]
                        labels.add(label)

                        if anno_type == 'boxes':
                            assert all([v in anno for v in ('xtl','ytl','xbr','ybr')])
                        elif anno_type == 'cuboids':
                            assert all([v in anno for v in ('xtl1','ytl1','xbl1','ybl1','xtr1','ytr1',
                                    'xbr1','ybr1','xtl2','ytl2','xbl2','ybl2','xtr2','ytr2','xbr2','ybr2')])
                        elif anno_type == 'polygons':
                            group = anno['group_id']
                            if group is not None:
                                assert isinstance(group, int) and group >= 0
                            for polygon_obj in anno['objects']:
                                assert 'points' in polygon_obj and len(polygon_obj['points']) % 2 == 0
                        else:
                            assert 'points' in anno and len(anno['points']) % 2 == 0

    is_zip = zipfile.is_zipfile(file_path)
    try:
        if is_zip:
            with zipfile.ZipFile(file_path,"r") as zf:
                for filename in zf.namelist():
                    if filename.endswith('.json'):
                        with zf.open(filename) as f:   
                            json_data = json.loads(f.read().decode("utf-8"))
                            get_labels(json_data)
        else:
            get_labels(json.load(open(file_path)))
    except Exception as e:
        raise Exception(f"Couldn't find mindkosh annotations at {file_path}")

    return labels


def validate_kitti_datasets(file_path):
    """Returns labels present in datasets
    """
    #TODO: Needs to be updated according to the new mindkosh_3d format
    labels = set()
    def get_labels(tracklets):
        tracklet_json = json.loads(tracklets)
        annotations = tracklet_json['boost_serialization']['tracklets']['item']
        for anno in annotations:
            labels.add(anno['objectType'])
            assert all([v in anno for v in ('h','l','w','frame')])
            assert all([v in anno['poses']['item'] for v in ('tx','ty','tz','rx','ry','rz')])

    try:
        with zipfile.ZipFile(file_path,"r") as zf:
            label_attrspec = zf.read('label_attrspec.json')
            tracklet_labels = zf.read('tracklet_labels.json')
            segmentations = zf.read('segmentations.json')
            frame_list = zf.read('frame_list.txt')
            
            label_items = json.loads(label_attrspec)
            get_labels(tracklet_labels)
    except:
        raise Exception(f"Couldn't find kitti annotations at {file_path}")

    return labels
        