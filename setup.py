#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup
from os import getenv

core_dependencies = [
    'opencv-python',
    'numpy',
    'Pillow',
    'terminaltables',
    'pytest',
    'pyrav4l2 @ git+https://github.com/antmicro/pyrav4l2.git'
]

setup(
    name='Raviewer',
    version='1.0',
    author='Antmicro Ltd',
    description="Tool for visualization of raw graphics data",
    author_email='contact@antmicro.com',
    url='https://github.com/antmicro/raviewer',
    license='Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'raviewer = raviewer.__main__:main',
        ]
    },
    install_requires=core_dependencies + ([] if getenv("NO_GUI", True) else ['dearpygui==1.1.1']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
