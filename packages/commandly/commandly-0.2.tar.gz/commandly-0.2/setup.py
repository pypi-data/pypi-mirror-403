from setuptools import setup, find_packages

setup(
    name="commandly",
    version="0.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "commandly=commandly.cli:main",
        ]
    },
)