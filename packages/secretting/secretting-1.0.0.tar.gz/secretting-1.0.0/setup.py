from io import open
from setuptools import setup, find_packages

name = 'secretting'
version = '1.0.0'
desc = 'secretting tools'


setup(
    name=name,
    version=version,
    description=desc,
    long_description=desc,
    py_modules=['secretting'],
    requires=[],
    packages=find_packages(),
)