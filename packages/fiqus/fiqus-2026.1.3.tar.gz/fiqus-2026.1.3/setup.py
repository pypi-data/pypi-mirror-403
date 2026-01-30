from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent

long_description = (this_dir / "README.md").read_text(encoding="utf-8")

install_requires = [
    "gmsh==4.15.0",
    "h5py>=3.10,<4",
    "Jinja2>=3.1,<4",
    "matplotlib>=3.8,<4",
    "mplcursors>=0.5,<1",
    "numpy>=1.26,<2",
    "pandas>=2.2,<3",
    "pydantic>=2.6,<3",
    "ruamel.yaml>=0.18,<1",
    "scipy>=1.14,<2",
    "tqdm>=4.66,<5",
]

docs_require = [
    "griffe==0.42.0",
    "markdown==3.5.2",
    "markdown-include==0.8.1",
    "mkdocs-git-revision-date-localized-plugin==1.2.4",
    "mkdocs-include-markdown-plugin==6.0.4",
    "mkdocs-material==9.5.13",
    "mkdocstrings-python==1.9.0",
    "mkdocs-autorefs==1.3.1",
]

tests_require = [
    "coverage==7.4.4",
    "coverage-badge==1.1.0",
    "flake8==7.0.0",
    "mypy==1.9.0",
    "pylint==3.1.0",
    "pytest==8.1.1",
    "pytest-cov==4.1.0",
    "pytest-subtests==0.12.1",
]

build_require = [
    "setuptools==69.2.0",
    "wheel==0.45.1",
    "twine==6.0.1",
]

setup(
    name="fiqus",
    version="2026.1.3",
    author="STEAM Team",
    author_email="steam-team@cern.ch",
    description="Source code for STEAM FiQuS tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.cern.ch/steam/fiqus",
    keywords=["STEAM", "FiQuS", "CERN"],
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        "docs": docs_require,
        "tests": tests_require,
        "build": build_require,
        "all": install_requires + docs_require + tests_require + build_require,
    },
    include_package_data=True,
    package_data={"fiqus": ["**/*.pro"]},
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
)
