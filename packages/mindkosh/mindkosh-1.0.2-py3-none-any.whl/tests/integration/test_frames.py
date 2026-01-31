import os
from PIL import Image


def test_frames(client, Label, random_str):
    resourceDir = '../assets/images/'
    task = client.task.create(
        name=random_str(),
        labels=(
            Label(
                name="penguin",
                color="#000000"
            ),
        ),
        resources=[os.path.abspath(resourceDir)],
        segment_size=2
    )

    frames = task.frames
    assert len(frames) == len(os.listdir(resourceDir))

    for frame_id, frame_obj in frames.items():
        im = Image.open(resourceDir + frame_obj.name)
        w, h = im.size
        assert frame_obj.width == w
        assert frame_obj.height == h

    task.delete()
