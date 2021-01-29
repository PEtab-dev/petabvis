"""Setuptools module for petabvis"""

import pathlib

from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    long_description=long_description,
    long_description_content_type='text/markdown',
)
