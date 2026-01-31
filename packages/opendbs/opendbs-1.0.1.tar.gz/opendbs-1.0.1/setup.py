from setuptools import setup, find_packages
import os

# Read README.md for the long description
with open(os.path.join(os.path.dirname(__file__), "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="opendbs",
    version="1.0.1",
    description="Official Python Client for OpenDBS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpenDBS Team",
    author_email="support@opendbs.in",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
