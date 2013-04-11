#!/usr/bin/env python
import os
from distutils.core import setup

def split(path, result=None):
    """
    Split a path into components in a platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return split(head, [tail] + result)

ROOT = os.path.dirname(__file__)
target_dirs = ['ceilometer_horizon']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

for target_dir in target_dirs:
    for dirpath, dirnames, filenames in os.walk(target_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'):
                del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(split(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f)
                               for f in filenames]])

setup(name="ceilometer_horizon",
      version="0.1",
      description="A ceilometer module that can be plugged into horizon.",
      author="Brooklyn Chen",
      author_email="brooklyn.chen@canonical.com",
      packages=packages,
      data_files=data_files,
      include_package_data=True
      )

