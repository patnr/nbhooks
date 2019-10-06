from setuptools import setup
from pathlib import Path

this_dir = Path(__file__).parent

# Load package version
with this_dir.joinpath("src/nbhooks.py").open(encoding="utf-8") as f:
    for line in f:
        d = {}
        try:
            exec(line, d)
        except Exception:
            continue
        try:
            version = d["__version__"]
            break
        except KeyError:
            continue
    else:
        raise Exception("__version__ not found in {}".format(f.name))


with this_dir.joinpath("README.md").open(encoding="utf-8") as f:
    long_description = f.read()

extras_require = {}
extras_require["dev"] = [
    "flake8 ~= 3.7",
    "ipython",
    "pre-commit ~= 1.18",
    "pytest ~= 5.1",
]

setup(
    name="nbhooks",
    version=version,
    description="Pre-commit hooks for Jupyter notebooks",
    long_description=long_description,
    license="MIT",
    author="Piotr Janiszewski",
    author_email="i.am.like.me@gmail.com",
    url="https://gitlab.com/iamlikeme/nbhooks",
    package_dir={"": "src"},
    py_modules=["nbhooks"],
    python_requires="~= 3.5",
    install_requires=[
        "click >= 7.0",
        "nbformat ~= 4.0",
    ],
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "nb-ensure-clean=nbhooks:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Framework :: Jupyter",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Version Control :: Git",
    ],
)
