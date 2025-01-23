"""Setup configuration for url2md package."""
from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        packages=find_packages(where="src"),
        package_dir={"": "src"},
    )