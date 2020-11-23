"""Setuptools module for petabvis"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='petabvis',
    version='0.0.0',
    description='Interactive visualization of PEtab problems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ICB-DCM/petab-interactive-viz',
    classifiers=[
        'Development Status :: 3 - Alpha',
    ],
    keywords='petab, visualization',
    packages=find_packages(where='petabvis'),
    python_requires='>=3.7, <4',
    install_requires=[
        'pandas==1.1.2',
        'petab>=0.1.8',
        'PySide2>=5.15.1',
        'PyYAML>=5.3.1',
        'pyqtgraph>=0.11.0'
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'petabvis=petabvis.pyqtgraph_test:main',
            'petabvis2=petabvis.main:main',
        ],
    },

    project_urls={
        'Bug Reports':
            'https://github.com/ICB-DCM/petab-interactive-viz/issues',
        'Source': 'https://github.com/ICB-DCM/petab-interactive-viz',
    },
)
