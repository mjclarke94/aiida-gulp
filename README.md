[![Build Status](https://travis-ci.org/chrisjsewell/aiida-gulp.svg?branch=master)](https://travis-ci.org/chrisjsewell/aiida-gulp)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/aiida-gulp/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/aiida-gulp?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-gulp/badge)](http://aiida-gulp.readthedocs.io/)
[![PyPI](https://img.shields.io/pypi/v/aiida-gulp.svg)](https://pypi.python.org/pypi/aiida-gulp/)
[![Anaconda](https://anaconda.org/conda-forge/aiida-gulp/badges/version.svg)](https://anaconda.org/conda-forge/aiida-gulp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# aiida-gulp

AiiDA plugin for running the [GULP](http://gulp.curtin.edu.au) code.

**Documentation**: https://readthedocs.org/projects/aiida-gulp

## Installation

To install from Conda (recommended)::

```shell
>> conda install -c conda-forge aiida-gulp aiida-core.services
```

To install from pypi::

```shell
>> pip install aiida-gulp
```

To install the development version:

```shell
>> git clone https://github.com/chrisjsewell/aiida-gulp .
>> cd aiida-gulp
>> pip install -e .  # also installs aiida, if missing (but not postgres)
>> #pip install -e .[pre-commit,testing] # install extras for more features
>> verdi quicksetup  # set up a new profile
>> verdi calculation plugins  # should now show the calculation plugins (with prefix gulp.)
```

## Development

### Testing against mock GULP executables

Because GULP is a licensed software, it is not possible to source a copy of the executable on Travis CI.
Therefore, a mock executable (`gulp_mock`) has been created for testing purposes (which also speeds up test runs).

This executable computes the md5 hash of the supplied input file and tries to match it against a dictionary of
precomputed hashes. If found, the executable will write the matching output (from `test/output_files`) to stdout.

The following will discover and run all unit test:

```shell
>> pip install -e .[testing]
>> reentry scan -r aiida
>> pytest -v
```

To omit tests which call external executables (like `gulp`):

```shell
>> pytest --gulp-skip-exec
```

To call the actual executable (e.g. `gulp` instead of `gulp_mock`):

```shell
>> pytest --gulp-no-mock
```

To output the results of calcjob executions to a specific directory:

```shell
>> pytest --gulp-workdir "test_workdir"
```

### Coding Style Requirements

The code style is tested using [flake8](http://flake8.pycqa.org),
with the configuration set in `.flake8`, and code should be formatted with [black](https://github.com/ambv/black).

Installing with `aiida-gulp[code_style]` makes the [pre-commit](https://pre-commit.com/)
package available, which will ensure these tests are passed by reformatting the code
and testing for lint errors before submitting a commit.
It can be setup by:

```shell
>> cd aiida-gulp
>> pre-commit install
```

Optionally you can run `black` and `flake8` separately:

```shell
>> black .  # recursively find and format files in-place
>> flake8
```

Editors like VS Code also have automatic code reformat utilities, which can adhere to this standard.

## License

See ``LICENSE`` file

## Contact

chrisj_sewell@hotmail.com
