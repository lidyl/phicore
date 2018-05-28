# -*- coding: utf-8 -*-
# CeCILL-B license LIDYL, CEA

from setuptools import setup, find_packages
import phicore

setup(
    name='phicore',
    version=phicore.__version__,
    packages=find_packages(),
    author="LIDYL CEA",
    description="Spatio temporal laser metrology package",
    long_description=open('README.rst').read(),
)
