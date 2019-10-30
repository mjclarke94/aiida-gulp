Changelog
=========

v0.10.0b5 (2019-10-18)
----------------------

- Programatically Access Resource Files:

  Non-python files (JSON schema and raw files) are now accessed programatically,
  using the `importlib_resources` package.
  This means that (a) they can be accessed even if the package is zipped and,
  (b) these files can be moved to a separate package in the future.

- Replace Travis flake8/version tests with a pre-commit test:

  - Updated `pre-commit` and `yapf` versions have been updated, and
  - `pre-commit run -a` has been applied to the repository.
  - Added conda test, to check the `conda_dev_env.yml` works.

- GULP: improve ReaxFF parser:

  - correctly handle read/write of ``X`` symbol
  - allow reaxff tolerance value to be set, when reading file to dict.

v0.9.2b5 (2019-08-01)
---------------------

- Add licence to all python files and pre-commit format.
- Change copyright license.
- Allow for 'trigonal' and 'rhombohedral' crystal types in gulp geometry
  input (these are subsets of 'hexagonal').


v0.9.1b5 (2019-07-25)
---------------------

- add ``doc8`` to ``pre-commit`` and fix ``conda_dev_env.yaml``
- Improve getting started documentation.
- Fix heading levels.
- Improve install and development instructions.
- Add pip dev install of root package to conda usage instuctions.
- Add ``aiida-core.services`` to conda development environment.
- Upgrade ipypublish dependancy to 0.10.7.
- Update pre-commit configuration and upgrade RTD's to Sphinx v2 (#14)


v0.9.0b5 (2019-07-18)
---------------------

- Upgraded to aiida-core==1.0.0b5.
- Record the order of configuration names in the ``gulp.fitting`` results
  node.
- Output a new potential, resulting from the ``gulp.fitting``
- Hard code breaking terms in ``read_atom_section``
- Add line breaking (with ``&``) to reaxff potential lines longer than 78
  characters.
- Add reading of lennard potential files.
- Format lennard-jones number valuesin input file.
- Fix reading gulp tables that have values replaced with
  \*\*\*\*\*\*\*s.

  Sometimes values can be output as \*'s (presumably if they are too large)
- Added functionality to run GULP calculations with 1-d structures.
- Add a settings input node to ``GulpFittingCalculation``
- Update package version in tests.
- Add extra info to fitting parser.
- Rewrote GULP execution and parsing.

  - The input file is no streamed to ``gulp`` via stdin and outputs are captured from stdout and stderr.
  - Single/Opt raw parser rewrote, to be inline with fitting parser
  - Exit codes updated and added
  - stderr file read and added to 'warnings' key of results
  - added dump file to fitting output
  - made calculation have data_regression checks.
- Store names of files in potential repo (rather than using class
  attributes)
- Retrieve fitting flag info from potential creation, and store
  potential dict in repo (rather than as attributes)
- Added input creation for reaxff fitting.
- Added output of fitting.
- Finalised creation of fitting input file (implemented for ``lj``)
- Add checks for index keys.
- Refactored reaxff keys and gulp write (in preparation for adding
  fitting flags)
- Create gulp_fitting_flags.yaml.
- Store full potential file in PotentialData (rather than creating on
  calculation submission)

  Then we don't have to rely on the external modules being there at calculation time.
  Also change potential keys from ``id1.id2`` to ``id1-id2`` (since AiiDa doesn't allow attributes with '.'s)
- Standardised GULP potentials.

  All potentials should share the a common jsonschema

  Also added reaxff tests, and initial implementation of fitting calculation.
- Restructure gulp raw test files.
- Move test files to correct place.
- Ensure cif to structure conversion provenance is stored.
- Add some helpful methods for manipulating StructureData.


v0.6.0b3 (2019-06-22)
---------------------
- Improve fractional <-> cartesian conversion.

  Use efficient numpy functions.
- Use kinds from input structure, in ``gulp.optimize`` parser.
- Fix  ``gulp.optimize`` parser, if the optimisation does not converge.

  - ensure the correct exit_code is returned
  - ensure the output cif is still read, and the output structure node created
  - add test.
- Add gulp potential class to entry points.
- Add EmpiricalPotential node type for gulp potential input.
- Use ase for cif converter.
- Move structure creation in tests to pytest fixture.
- Add an exit code for non optimised calculations.
- Fix symmetry restricted computations for GULP.

  When including symmetry restrictions in GULP input files,
  only symmetry inequivalent sites (and) positions should be listed.
  We parse these in the symmetry input node.
- Retrieve input file for GULP computations.
- Add method for getting the spacegroup info of a symmetry node.
- Require correct symmetry input node type (gulp.symmetry)
- Remove pypi deployment flag from python=2.7 tests.


v0.5.0b3 (2019-06-13)
---------------------
- Add GULP calculations (#4)

  - update aiida-core to v1.0.0b3
  - added GULP calculations, tests and documentation
  - add dependencies for reading CIF files
  - implement calculation submission tests (using process.prepare_for_submission)
  - implement new calculation immigration method
  - re-number calculation exit codes
  - update readthedocs build.
