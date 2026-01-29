#!/usr/bin/env python3

# File: setup.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2026-01-25
# Description: 
# License: MIT

from setuptools import setup, find_packages
import os

try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

# Read the long description from README
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Handle Cython extensions
ext_modules = []
if USE_CYTHON:
    ext_modules = cythonize(
        "qviewer/viewer.pyx",
        compiler_directives={
            'language_level': "3",
            'embedsignature': True,
        }
    )

setup(
    name='qviewer',
    version='0.2.0',
    author='Hadi Cahyadi',
    author_email='cumulus13@gmail.com',
    description='A fast PyQt5-based image viewer with URL support',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cumulus13/qviewer',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Cython',
    ],
    python_requires='>=3.7',
    install_requires=[
        'PyQt5>=5.15.0',
        'requests>=2.25.0',
        'clipboard>=0.0.4',
    ],
    entry_points={
        'console_scripts': [
            'qviewer=qviewer.main:main',
            'qv=qviewer.main:main',
        ],
    },
    setup_requires=['cython>=0.29.0'] if USE_CYTHON else [],
    ext_modules=ext_modules,
    include_package_data=True,
    zip_safe=False,
)
