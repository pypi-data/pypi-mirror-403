#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="sesamo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'torch>=0.4.1',
        'numpy',
        'tqdm',
        'matplotlib',
        'tensorboard',
        'hydra-core',
        'hydra-submitit-launcher',
        'nflows'
    ],
)