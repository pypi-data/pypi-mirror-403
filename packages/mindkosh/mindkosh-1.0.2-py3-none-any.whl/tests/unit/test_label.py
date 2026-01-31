import pytest
from mindkosh import exceptions


def test_duplicate_label(Label):
    labels = [
        Label(
            name="l1",
            color="#fff000",
            attributes=[]
        ),
        Label(
            name="l1",
            color="#f00000"
        )
    ]

    with pytest.raises(exceptions.InvalidLabelError) as msg:
        Label.verify(
            labels=labels
        )


def test_invalid_label_color(Label):
    labels = [
        Label(
            name="l1",
            color="#fff00z",
            attributes=[]
        ),
        Label(
            name="l2",
            color="#f00000"
        )
    ]

    with pytest.raises(exceptions.InvalidLabelError) as msg:
        Label.verify(
            labels=labels
        )


@pytest.mark.skip
def test_label_attributes(Label, Attribute):
    pass
