import os
from setuptools import setup, find_packages


def read(rel_path: str) -> str:
    """Read a file relative to the setup.py location.

    Parameters
    ----------
    rel_path : str
        Relative path to the file from setup.py location.

    Returns
    -------
    str
        The contents of the file as a string.
    """
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), encoding="utf-8") as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    """Extract version string from a Python file.

    Parameters
    ----------
    rel_path : str
        Relative path to the Python file containing version info.

    Returns
    -------
    str
        The version string.

    Raises
    ------
    RuntimeError
        If version string cannot be found.
    """
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


# Determine version from either version.py or __init__.py
version_file = (
    "lcurvetools/version.py"
    if os.path.exists("lcurvetools/version.py")
    else "lcurvetools/__init__.py"
)
VERSION = get_version(version_file)

setup(
    name="lcurvetools",
    version=VERSION,
    description=(
        "Simple Python tools for plotting learning curves of neural network"
        " models trained with the Keras, Ultralytics YOLO or scikit-learn"
        " framework in a single figure in an easy-to-understand format."
    ),
    author="Andriy Konovalov",
    author_email="kandriy74@gmail.com",
    license="BSD 3-Clause License",
    long_description=read("README.md") + "\n\n" + read("CHANGELOG.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/kamua/lcurvetools",
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires=">=3.10",
    install_requires=["numpy", "matplotlib", "scikit-learn"],
    packages=find_packages(exclude=("tests*", "test_*", "demo_notebooks*")),
    keywords=[
        "learning curve",
        "keras",
        "ultralytics yolo",
        "scikit-learn",
        "loss_curve",
        "validation_score",
    ],
)
