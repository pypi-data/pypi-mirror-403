from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="log2py",
    version="1.0.0",
    author="Kanowara Sinoka",
    author_email="sinok@sinoka.dev",
    description="A Simple Logging Library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sinokadev/log4py",
    packages=find_packages(),
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)