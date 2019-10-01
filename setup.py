from setuptools import setup, find_packages
from pathlib import Path

this_dir = Path(__file__).parent

with this_dir.joinpath("src/nbhooks/__version__.py").open(encoding="utf-8") as f:
    _temp = {}
    exec(f.read(), _temp)
    version = _temp.pop("__version__")

with this_dir.joinpath("README.md").open(encoding="utf-8") as f:
    long_description = f.read()

repo_url = "https://github.com/iamlikeme/pre-commit-hooks-jupyter/"

extras_require = {}
extras_require["test"] = ["pytest ~= 5.1"]
extras_require["dev"] = extras_require["test"] + [
    "flake8 ~= 3.7",
    "ipython",
    "pre-commit ~= 1.18",
]

setup(
    name="nbhooks",
    version=version,
    description="Pre-commit hooks for Jupyter notebooks",
    long_description=long_description,
    package_dir={"": "src"},
    packages=find_packages("src"),
    author="Piotr Janiszewski",
    author_email="i.am.like.me@gmail.com",
    url=repo_url,
    license="MIT",
    download_url=repo_url + "archive/v{}".format(version),
    classifiers=[],
    python_requires="~= 3.5",
    install_requires=["nbformat ~= 4.0"],
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "nbhooks=nbhooks.cli:main",
        ],
    },
)
