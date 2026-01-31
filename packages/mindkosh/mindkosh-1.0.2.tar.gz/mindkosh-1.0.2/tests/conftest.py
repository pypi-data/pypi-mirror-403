import pytest
import os
import random
import string
import dotenv

import mindkosh

dotenv.load_dotenv()

# @pytest.fixture


def token():
    try:
        return os.environ.get('MK_SDK_TOKEN', None)
    except KeyError:
        raise Exception("could not find token")


@pytest.fixture
def client():
    return mindkosh.Client(token())


@pytest.fixture
def Label():
    return mindkosh.Label


@pytest.fixture
def TestSet():
    return mindkosh.TestSet


@pytest.fixture
def PointCloudFile():
    return mindkosh.PointCloudFile


@pytest.fixture
def RelatedFile():
    return mindkosh.RelatedFile


@pytest.fixture
def random_str():
    def name(length=0):
        length = random.randint(2, 8) if not length else length
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return name
