import os
import json
import tempfile
import shutil


def gen_tempDir():
    return tempfile.mkdtemp()


def remove_tempDir(tempDir):
    shutil.rmtree(tempDir)


def test_frames_annotations(client, Label, TestSet, random_str):
    resourceDir = '../assets/images/'
    segment_size = 2
    task = client.task.create(
        name=random_str(),
        labels=(
            Label(
                name="penguin",
                color="#000000"
            ),
        ),
        resources=[os.path.abspath(resourceDir)],
        segment_size=segment_size
    )

    frames = task.frames
    # size = 4
    testset = TestSet()
    frame_ids = [0, 1, 3]
    frames_to_visualize = [frames[frame_id] for frame_id in frame_ids]
    testset.add(frames_to_visualize)

    tempdir = gen_tempDir()
    print(tempdir)
    filename = random_str() + ".json"
    testset.download_annotations(
        location=tempdir,
        format=None,
        filename=filename
    )

    f = open(os.path.join(tempdir, filename))
    data = json.load(f)

    assert len(data) == 1

    annotations = data[0]

    assert "version" in annotations
    assert "tags" in annotations
    assert "tracks" in annotations
    assert "task_id" in annotations
    assert annotations["task_id"] == task.task_id
    assert "shapes" in annotations

    shapes = annotations["shapes"]

    frames_in_annotations = set()
    for shape in shapes:
        frames_in_annotations.add(shape["frame"])

    assert frames_in_annotations == set(frame_ids)

    remove_tempDir(tempdir)
    task.delete()


def test_cross_task_frames_annotations(client, Label, TestSet, random_str):
    resourceDir = '../assets/images/'

    task1 = client.task.create(
        name=random_str(),
        labels=(
            Label(
                name="l1",
                color="#000000"
            ),
        ),
        resources=[os.path.abspath(
            resourceDir + 'l1.jpg'), os.path.abspath(resourceDir + 'l2.jpg')]
    )

    task2 = client.task.create(
        name=random_str(),
        labels=(
            Label(
                name="l2",
                color="#000000"
            ),
        ),
        resources=[os.path.abspath(
            resourceDir + 'l3.jpg'), os.path.abspath(resourceDir + 'l4.png')]
    )
    task1_frames = task1.frames
    task2_frames = task2.frames
    # size = 4
    testset = TestSet()
    testset.clear()
    frames_to_visualize = [task1_frames[0],
                           task1_frames[1], task2_frames[0], task2_frames[1]]
    testset.add(frames_to_visualize)

    tempdir = gen_tempDir()
    print(tempdir)
    filename = random_str() + ".json"
    testset.download_annotations(
        location=tempdir,
        format=None,
        filename=filename
    )

    f = open(os.path.join(tempdir, filename))
    data = json.load(f)

    assert len(data) == 2

    for annotations in data:
        assert "version" in annotations
        assert "tags" in annotations
        assert "tracks" in annotations
        assert "task_id" in annotations
        assert "shapes" in annotations
        if annotations["task_id"] == task1.task_id:
            task1_annotations = annotations
        if annotations["task_id"] == task2.task_id:
            task2_annotations = annotations

    task1_shapes = task1_annotations["shapes"]
    task2_shapes = task2_annotations["shapes"]

    task1_frames_in_annotations = set()
    task2_frames_in_annotations = set()
    for shape in task1_shapes:
        task1_frames_in_annotations.add(shape["frame"])
    for shape in task2_shapes:
        task2_frames_in_annotations.add(shape["frame"])

    assert task1_frames_in_annotations == {0, 1}
    assert task2_frames_in_annotations == {0, 1}

    remove_tempDir(tempdir)
    task1.delete()
    task2.delete()
