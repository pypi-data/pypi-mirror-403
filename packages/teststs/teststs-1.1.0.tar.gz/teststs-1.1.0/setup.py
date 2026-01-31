from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="teststs",
    version="1.1.0",
    author="Kanowara Sinoka",
    author_email="sinok@sinoka.dev",
    description="A Simple, Tiny Test Library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sinokadev/teststs",
    packages=find_packages(),
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
