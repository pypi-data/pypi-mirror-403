from setuptools import setup, find_packages
from setup_utils import read_version

version = read_version()

setup(
    name="devbricksx",
    version=version,
    author="Daily Studio",
    author_email="dailystudio2010@gmail.com",
    description="DevBricks X Python provides several classes which will usually be used in everyday Python development",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dailystudio/devbricksx-py",
    packages=find_packages(include=["devbricksx", "devbricksx.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    license="Apache License 2.0",
    python_requires=">=3.6",
    install_requires=[
        "Pillow>=10.2.0",
        "numpy",
        "jsons",
        "filetype",
        "typish"
    ],
)