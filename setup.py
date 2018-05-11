#!/usr/bin/env python
import subprocess

import sys

import os
from setuptools import setup, find_packages, Command


setup(name='git-feature',
      version='0.1.0',
      description='Handle feature branches for onnx and caffe2 repositories',
      author='Sebastian Messmer',
      author_email='messmer@fb.com',
      license='GPLv3',
      url='https://github.com/smessmer/onnx-git-flow',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
          'git-feature = onnx_git_feature.__main__:main'
        ],
      },
      install_requires=[
        'typing',
        'argparse',
        'typing',
        'typing-extensions',
      ],
      classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
      ],
)
