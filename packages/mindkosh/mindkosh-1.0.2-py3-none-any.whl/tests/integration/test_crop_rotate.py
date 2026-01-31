import os
import pytest
from PIL import Image


@pytest.mark.skip
def test_crop_rotate(client, Label, random_str):
    manifestfile = os.path.abspath('../assets/manifest.json')
    task = client.task.create(
        name=random_str(),
        labels=(
            Label(
                name="penguine",
                color="#000000"
            ),
        ),
        manifest=manifestfile,
        segment_size=2
    )

    frames = task.frames
    assert len(frames) == 4

    l1 = Image.open('../assets/images/l1.jpg')
    l2 = Image.open('../assets/images/l2.jpg')
    l3 = Image.open('../assets/images/l3.jpg')
    l4 = Image.open('../assets/images/l4.png')

    for frame in frames.values():
        if frame.name == "l1.jpg":
            w, h = l1.size
            # rotated by 90
            # h,w = w,h
        elif frame.name == "l2.jpg":
            w, h = l2.size
            w -= 100
            h -= 100
        elif frame.name == "l3.jpg":
            w, h = l3.size
            w -= 100
        elif frame.name == "l4.png":
            w, h = l4.size
            # w,h = h,w

        assert frame.width == w
        assert frame.height == h

    task.delete()
