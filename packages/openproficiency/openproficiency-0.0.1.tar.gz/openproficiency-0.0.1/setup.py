"""Setup configuration for OpenProficiency library."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openproficiency",
    version="0.0.1",
    author="OpenProficiency Contributors",
    description="A library for managing proficiency topics and topic lists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openproficiency/openproficiency",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
