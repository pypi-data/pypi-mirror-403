from setuptools import setup, find_packages

setup(
    name="opendbs",
    version="1.0.0",
    description="Official Python Client for OpenDBS",
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
