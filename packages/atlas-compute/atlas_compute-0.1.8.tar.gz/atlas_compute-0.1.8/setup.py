"""Setup script for Atlas SDK."""

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="atlas-compute",
    version="0.1.8",
    description="Atlas Compute SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Thomas Tsuma",
    author_email="tommytsuma7@gmail.com",
    url="https://github.com/coreoutline/atlas-compute",
    packages=["atlas_compute", "atlas_compute.repositories"],
    package_dir={"atlas_compute": "."},
    install_requires=[
        "pandas",
        "numpy",
        "clickhouse-driver",
        "matplotlib",
        "opensearch-py",
        "minio",
        "requests",
        "fastapi",
        "python-dotenv"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
