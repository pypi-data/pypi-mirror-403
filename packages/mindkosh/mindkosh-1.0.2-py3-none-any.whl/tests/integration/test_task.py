import pytest
import os
import json
import random
import string
import tempfile
import shutil
import numpy as np
from PIL import Image


def random_str(length=None):
    length = random.randint(2, 8) if not length else length
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def gen_color():
    color = "%06x" % random.randint(0, 0xFFFFFF)
    return f"#{color}"


def gen_labels(Label, n):
    labels = []
    for i in range(1, n+1):
        name = random_str(i)
        color = gen_color()
        label = Label(name=name, color=color)
        labels.append(label)
    return labels


def gen_tempDir():
    return tempfile.mkdtemp()


def remove_tempDir(tempDir):
    shutil.rmtree(tempDir)


def image_ext():
    return random.choice(('.jpg', '.jpeg', '.png'))


def gen_randomImage(tempDir):
    width = random.randint(400, 1000)
    height = random.randint(400, 1000)
    im = Image.new("RGB", (width, height), color=gen_color())
    name = random_str() + image_ext()
    fullname = os.path.join(tempDir, name)
    im.save(fullname)
    return fullname


def gen_randomImages(tempDir, n=0):
    n = random.randint(2, 8) if n == 0 else n
    for _ in range(n):
        gen_randomImage(tempDir)


def gen_manifest(rootTempDir):
    manifestFile = os.path.join(rootTempDir, random_str()+".json")
    with open(manifestFile, 'w') as fp:
        pass
    data = {}

    # images
    images = []
    for _ in range(random.randint(1, 4)):
        imagepath = gen_randomImage(rootTempDir)
        images.append({
            "path": imagepath,
            "crop": (50, 50, 50, 50),
            "rotate": random.choice((180, 90, 270))
        })
    data["images"] = images

    # folders
    folders = []
    for _ in range(random.randint(1, 4)):
        path = os.path.join(rootTempDir, random_str())
        os.mkdir(path)
        gen_randomImages(path)
        folders.append({
            "path": path,
            "rotate": random.choice((180, 90, 270)),
            "crop": (0, 0, 50, 50)
        })
    data["folders"] = folders

    with open(manifestFile, 'w') as f:
        json.dump(data, f, indent=4)

    return manifestFile


def gen_recursiveDir(tempDir, depth):
    dir = tempDir
    if depth:
        image_count = random.randint(2, 5)
        gen_randomImages(dir, image_count)
        innerDir = os.path.join(dir, random_str())
        os.mkdir(innerDir)
        gen_recursiveDir(innerDir, depth-1)
    else:
        return



def test_manifest(client, Label):
    # before
    tasks = client.task.get()
    for t in tasks:
        assert isinstance(t, client.task)

    ### create ###
    name = random_str()
    labels = gen_labels(Label, random.randint(1, 4))
    # create tempdir
    rootTempDir = gen_tempDir()

    manifest = gen_manifest(rootTempDir)
    image_count = sum([len(files)
                      for base, dirs, files in os.walk(rootTempDir)]) - 1
    segment_size = random.randint(2, 6)

    new_task = client.task.create(
        name=name,
        labels=labels,
        manifest=manifest,
        segment_size=segment_size
    )

    remove_tempDir(rootTempDir)

    new_task_id = new_task.task_id

    assert new_task.name == name
    assert new_task.segment_size == segment_size
    assert new_task.size == image_count
    # after
    updated_tasks = client.task.get()
    assert len(updated_tasks) == len(tasks) + 1
    updated_ids = []
    for t in updated_tasks:
        updated_ids.append(t.task_id)
    assert new_task_id in updated_ids

    # labels
    assert len(new_task.labels) == len(labels)
    labels_ = []
    for label in new_task.labels:
        labels_.append({"name": label.name, "color": label.color})
    pairs = zip([label.__dict__ for label in labels], labels_)
    assert not any(x != y for x, y in pairs)

    ### update ###
    new_name = random_str()
    new_task.update_name(
        name=new_name
    )
    assert new_task.name == new_name

    ### delete task ###
    new_task.delete()
    updated_tasks = client.task.get()
    assert len(updated_tasks) == len(tasks)
    updated_ids = []
    for t in updated_tasks:
        updated_ids.append(t.task_id)
    assert new_task_id not in updated_ids


def test_image_task(client,Label):
    tasks = client.task.get()
    for t in tasks:
        assert isinstance(t, client.task)

    ### create ###
    name = random_str()
    labels = gen_labels(Label, random.randint(1, 4))
    dataset_id = 1 #get_image_dataset_id()

    task_status = client.task.create(
        name = name,
        labels = labels,
        dataset_id = dataset_id
    )

    assert task_status.lower() == "finished"

    updated_tasks = client.task.get()
    assert len(updated_tasks) == len(tasks) +1

    new_task = updated_tasks[0]

    assert new_task.name == name
    #assert new_task.labels== labels
    assert new_task.category == 'image'
    assert new_task.batches == 1
    assert new_task.project_id == None
    assert new_task.data['dataset']['id'] == dataset_id

    new_task.delete()


def test_pointcloud_task(client,Label):
    tasks = client.task.get()
    for t in tasks:
        assert isinstance(t, client.task)

    ### create ###
    name = random_str()
    labels = gen_labels(Label, random.randint(1, 4))
    dataset_id = 1 #get_pcd_dataset_id()

    task_status = client.task.create(
        name = name,
        labels = labels,
        dataset_id = dataset_id
    )

    assert task_status.lower() == "finished"

    updated_tasks = client.task.get()
    assert len(updated_tasks) == len(tasks) +1

    new_task = updated_tasks[0]

    assert new_task.name == name
    #assert new_task.labels== labels
    assert new_task.category == 'pointcloud'
    assert new_task.batches == 1
    assert new_task.project_id == None
    assert new_task.data['dataset']['id'] == dataset_id

    new_task.delete()