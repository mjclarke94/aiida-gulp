Installation
++++++++++++

|PyPI| |Conda|

To install from Conda (recommended)::

    >> conda install -c conda-forge aiida-gulp aiida-core.services

To install from pypi::

    >> pip install --pre aiida-gulp

To install the development version::

    >> git clone https://github.com/chrisjsewell/aiida-gulp .
    >> cd aiida-gulp

and either use the pre-written Conda development environment (recommended)::

    >> conda env create -n aiida_testenv -f conda_dev_env.yml python=3.6
    >> conda activate aiida_testenv
    >> pip install --no-deps -e .

or install all *via* pip::

    >> pip install -e .  # note this won't install postgres and rabbitmq
    #>> pip install -e .[code_style,testing,docs] # install extras for more features

To configure aiida::

    >> rabbitmq-server -detached >/dev/null 2>&1
    >> eval "$(_VERDI_COMPLETE=source verdi)"
    >> verdi quicksetup  # better to set up a new profile
    >> verdi status
    >> verdi calculation plugins  # should now show your calclulation plugins

Then use ``verdi code setup`` with a ``gulp.`` input plugin
to set up an AiiDA code for that plugin.

.. seealso::

    The `AiiDA documentation <http://aiida-core.readthedocs.io>`_,
    for more general information on configuring and working with AiiDa.

GULP Executable
+++++++++++++++

For test purposes, the ``gulp_mock`` executable
is installed with ``aiida-gulp``, that will return pre-computed output files,
if parsed specific test input files (based on the contents hash).
When running the test suite, these executable will be used in place of ``gulp``,
unless ``pytest --gulp-no-mock`` is used.

Development
+++++++++++

Testing
~~~~~~~

|Build Status| |Coverage Status|

The following will discover and run all unit test:

.. code:: shell

   >> cd aiida-gulp
   >> pytest -v

To omit tests which call external executables (like ``gulp``):

.. code:: shell

   >> pytest --gulp-skip-exec

To call the actual executables (e.g. ``gulp`` instead of ``gulp_mock``):

.. code:: shell

   >> pytest --gulp-no-mock

To output the results of calcjob executions to a specific directory:

.. code:: shell

   >> pytest --gulp-workdir "test_workdir"

Coding Style Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~

The code style is tested using `flake8 <http://flake8.pycqa.org>`__,
with the configuration set in ``.flake8``, and
`black <https://github.com/ambv/black>`__.

Installing with ``aiida-gulp[code_style]`` makes the
`pre-commit <https://pre-commit.com/>`__ package available, which will
ensure these tests are passed by reformatting the code and testing for
lint errors before submitting a commit. It can be setup by:

.. code:: shell

   >> cd aiida-gulp
   >> pre-commit install

Optionally you can run ``black`` and ``flake8`` separately:

.. code:: shell

   >> black path/to/file  # format file in-place
   >> flake8

Editors like VS Code also have automatic code reformat utilities, which
can check and adhere to this standard.

Documentation
~~~~~~~~~~~~~

The documentation can be created locally by:

.. code:: shell

   >> cd aiida-gulp/docs
   >> make clean
   >> make  # or make debug

.. |PyPI| image:: https://img.shields.io/pypi/v/aiida-gulp.svg
   :target: https://pypi.python.org/pypi/aiida-gulp/
.. |Conda| image:: https://anaconda.org/conda-forge/aiida-gulp/badges/version.svg
   :target: https://anaconda.org/conda-forge/aiida-gulp
.. |Build Status| image:: https://travis-ci.org/chrisjsewell/aiida-gulp.svg?branch=master
   :target: https://travis-ci.org/chrisjsewell/aiida-gulp
.. |Coverage Status| image:: https://coveralls.io/repos/github/chrisjsewell/aiida-gulp/badge.svg?branch=master
   :target: https://coveralls.io/github/chrisjsewell/aiida-gulp?branch=master
