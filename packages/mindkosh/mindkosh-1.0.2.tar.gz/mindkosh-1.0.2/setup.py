# Copyright (C) 2024 Mindkosh Technologies. All rights reserved.
# Author: Shikhar Dev Gupta

from setuptools import setup, find_packages

def get_long_description():
    with open("README.md", "r") as fh:
        return fh.read()

def get_requirements():
    requirements = []
    with open('requirements.txt') as lines:
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

setup(
    name='mindkosh',
    version='1.0.2',
    description="Mindkosh Python SDK",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url='https://github.com/Mindkosh/mindkosh-python-sdk',
    author="Mindkosh",
    author_email="shikhar@mindkosh.com",
    packages=find_packages(),
    include_package_data=True,
    license="Apache-2.0",
    python_requires='>=3.7',
    install_requires=[
        "requests==2.31.0",
        "typing-extensions==4.7.1",
        "numpy==1.21.6",
        "Pillow==9.2.0",
        "kiwisolver==1.4.4",
        "matplotlib==3.5.1",
        "mplcursors==0.5.1",
        "aiohttp==3.8.6",
        "alive-progress==2.4.1",
        "validators==0.20.0",
        "python-dotenv==0.21.0"
    ],
    keywords=[
        "annotation",
        "segmentation",
        "pointcloud",
        "computervision",],
)
