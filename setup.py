#!/usr/bin/env python
from setuptools import setup, find_packages

from systempay import VERSION

setup(name='django-oscar-systempay',
      version=VERSION,
      url='https://github.com/peteralaoui/django-oscar-systempay',
      author="Pierre Dulac",
      author_email="pierre@friendcashapp.com",
      description="SystemPay Cyberplus payment module for django-oscar",
      long_description=open('README.rst').read(),
      keywords="Payment, SystemPay, Cyberplus, Oscar",
      license=open('LICENSE').read(),
      platforms=['linux'],
      packages=find_packages(exclude=['sandbox*', 'tests*']),
      include_package_data=True,
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: Unix',
                   'Programming Language :: Python'],
      install_requires=['django-oscar>=0.2',
                        'requests>=0.13.1',
                        'purl==0.4'],
      )
