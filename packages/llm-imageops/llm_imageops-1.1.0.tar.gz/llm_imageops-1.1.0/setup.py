"""Setup configuration for imageops package."""

from setuptools import setup, find_packages

# Read version from __init__.py
with open("imageops/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break

setup(
    name="llm-imageops",
    version=version,
    packages=find_packages(),
    python_requires=">=3.9",
)

