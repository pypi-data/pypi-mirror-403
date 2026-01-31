"""
Setup script for PyOptima.
"""

from setuptools import setup

# For direct invocation (python setup.py); src layout
if __name__ == "__main__":
    from setuptools import find_packages

    setup(
        package_dir={"": "src"},
        packages=find_packages(where="src"),
    )

