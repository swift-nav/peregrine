#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
  import sys
  reload(sys).setdefaultencoding("UTF-8")
except:
  pass

try:
  from setuptools import setup, find_packages
except ImportError:
  print 'Please install or upgrade setuptools or pip to continue.'
  sys.exit(1)

from version import get_git_version

INSTALL_REQUIRES = ['numpy >= 1.9',
                    'pyFFTW >= 0.8.2',
                    'scipy >= 0.13.3',
                    'swiftnav']

TEST_REQUIRES = ['pytest']

EXTRAS_REQUIRE = {'progress': ['progressbar >= 2.3'],
                  'plot': ['matplotlib >= 1.1'],}

setup(name='Peregrine',
      description='Peregrine software GNSS receiver',
      license='GPLv3',
      url='http://swiftnav.com',
      author='Swift Navigation Inc.',
      maintainer='Swift Navigation',
      maintainer_email='dev@swift-nav.com',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
          'peregrine = peregrine.run:main',
          'peregrine-analyze-samples = peregrine.analysis.samples:main',
          'peregrine-show-acq = peregrine.analysis.acquisition:main',
      ]
      },
      install_requires=INSTALL_REQUIRES,
      tests_require=TEST_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      platforms="Linux,Windows,Mac",
      use_2to3=False,
      zip_safe=False
)
