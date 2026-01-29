from setuptools import setup, find_packages

setup(
    name="myeda",
    version="0.1.13",
    packages=find_packages(include=["myeda", "myeda.*"]),
)

