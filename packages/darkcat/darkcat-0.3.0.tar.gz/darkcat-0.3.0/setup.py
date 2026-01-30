from setuptools import setup, find_packages

setup(
    name="darkcat",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "darkcat=darkcat.cli:cli"
        ]
    },
)
