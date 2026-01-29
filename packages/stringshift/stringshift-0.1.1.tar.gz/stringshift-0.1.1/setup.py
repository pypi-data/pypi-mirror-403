from setuptools import setup, find_packages

setup(
    name="stringshift",
    version="0.1.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "stringshift = stringshift.cli:main"
        ]
    },
)
