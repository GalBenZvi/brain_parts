========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/connectomeplasticity/badge/?style=flat
    :target: https://connectomeplasticity.readthedocs.io/
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.com/GalBenZvi/connectomeplasticity.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/github/GalBenZvi/connectomeplasticity

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/GalBenZvi/connectomeplasticity?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/GalBenZvi/connectomeplasticity

.. |requires| image:: https://requires.io/github/GalBenZvi/connectomeplasticity/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/GalBenZvi/connectomeplasticity/requirements/?branch=master

.. |codecov| image:: https://codecov.io/gh/GalBenZvi/connectomeplasticity/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/GalBenZvi/connectomeplasticity

.. |version| image:: https://img.shields.io/pypi/v/connectome-plasticity-project.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/connectome-plasticity-project

.. |wheel| image:: https://img.shields.io/pypi/wheel/connectome-plasticity-project.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/connectome-plasticity-project

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/connectome-plasticity-project.svg
    :alt: Supported versions
    :target: https://pypi.org/project/connectome-plasticity-project

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/connectome-plasticity-project.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/connectome-plasticity-project

.. |commits-since| image:: https://img.shields.io/github/commits-since/GalBenZvi/connectomeplasticity/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/GalBenZvi/connectomeplasticity/compare/v0.0.0...master



.. end-badges

A package to hold all CPP-related code

* Free software: MIT license

Installation
============

::

    pip install connectome-plasticity-project

You can also install the in-development version with::

    pip install https://github.com/GalBenZvi/connectomeplasticity/archive/master.zip


Documentation
=============


https://connectomeplasticity.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
