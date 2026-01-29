"""
Setup script for pyide-sdk package.

This file exists for backwards compatibility with older pip versions
and editable installs. The main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    name="pyide-sdk",
    version="1.0.0",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    python_requires=">=3.8",
    author="PyIDE Team",
    author_email="support@pyide.org",
    description="Plugin SDK for PyIDE - Create extensions and plugins for PyIDE",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AeonLtd/pyide-sdk",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
