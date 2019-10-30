"""pytest plugin configuration.

For more information on writing pytest plugins see:

- https://docs.pytest.org/en/latest/writing_plugins.html
- https://docs.pytest.org/en/latest/reference.html#request
- https://docs.pytest.org/en/latest/example/simple.html
- https://github.com/pytest-dev/cookiecutter-pytest-plugin

"""
import os
import shutil
import tempfile

from _pytest.config import Config  # noqa: F401
from _pytest.config.argparsing import Parser  # noqa: F401
from _pytest.nodes import Item  # noqa: F401
import pytest

from aiida.manage.fixtures import fixture_manager

from aiida_gulp.tests import get_test_structure, open_resource_binary
from aiida_gulp.tests.utils import AiidaTestApp

GULP_CALL_EXEC_MARKER = "gulp_calls_executable"
GULP_NOTEBOOK_MARKER = "gulp_doc_notebooks"

gulp_no_mock_HELP = "Do not use mock executables for tests."
GULP_WORKDIR_HELP = (
    "Specify a work directory path for aiida calcjob execution. "
    "If not specified, a temporary directory is used and deleted after tests execution."
)
GULP_SKIP_EXEC_HELP = "skip tests marked with @pytest.mark.{}".format(
    GULP_CALL_EXEC_MARKER
)
GULP_NB_TEST_HELP = "Only run tests marked {} (otherwise skipped)".format(
    GULP_NOTEBOOK_MARKER
)


class NotSet(object):
    """Indicate that a configuration file variable was not set."""


def pytest_addoption(parser):
    # type: (Parser) -> None
    """Define pytest command-line and configuration file options.

    Configuration file options are set in pytest.ini|tox.ini|setup.cfg as e.g.::

        [pytest]
        gulp_no_mock = false

    Configuration options can be accessed via the `pytestconfig` fixture::

        @pytest.fixture
        def my_fixture(pytestconfig)
            pytestconfig.getoption('gulp_no_mock')
            pytestconfig.getini('gulp_no_mock')

    """
    group = parser.getgroup("aiida_gulp")
    group.addoption(
        "--gulp-no-mock",
        action="store_true",
        dest="gulp_no_mock",
        default=False,
        help=gulp_no_mock_HELP,
    )
    group.addoption(
        "--gulp-workdir", dest="gulp_workdir", default=None, help=GULP_WORKDIR_HELP
    )
    group.addoption(
        "--gulp-skip-exec",
        action="store_true",
        dest="gulp_skip_exec",
        default=False,
        help=GULP_SKIP_EXEC_HELP,
    )
    group.addoption(
        "--gulp-nb-tests",
        action="store_true",
        dest="gulp_nb_tests",
        default=False,
        help=GULP_NB_TEST_HELP,
    )
    group.addoption(
        "--gulp-nb-tests-only",
        action="store_true",
        dest="gulp_nb_tests_only",
        default=False,
        help=GULP_NB_TEST_HELP,
    )

    parser.addini("gulp_no_mock", gulp_no_mock_HELP, type="bool", default=NotSet())
    parser.addini("gulp_workdir", GULP_WORKDIR_HELP, default=NotSet())


def use_mock_exec(config):
    """Return whether mock executables should be used."""
    if config.getoption("gulp_no_mock"):
        return False
    ini = config.getini("gulp_no_mock")
    return True if isinstance(ini, NotSet) else not ini


def get_work_directory(config):
    """Return the aiida work directory to use."""
    if config.getoption("gulp_workdir") is not None:
        return config.getoption("gulp_workdir")
    ini = config.getini("gulp_workdir")
    if isinstance(ini, NotSet):
        return None
    return ini


def pytest_configure(config):
    # type: (Config) -> None
    """Register pytest markers.

    These will show in ``pytest --markers``
    """
    config.addinivalue_line(
        "markers",
        "{}: mark tests that will call external executables".format(
            GULP_CALL_EXEC_MARKER
        ),
    )
    config.addinivalue_line(
        "markers",
        "{}: mark tests that will test document notebooks".format(GULP_NOTEBOOK_MARKER),
    )


def pytest_collection_modifyitems(config, items):
    # type: (Config, list) -> None
    """Modify collected test items (may filter or re-order the items in-place).

    If ``gulp_nb_tests_only == True``, deselect all tests not marked ``gulp_doc_notebooks``.

    Add skip marker to tests marked:

    - ``gulp_calls_executable`` if ``gulp_skip_exec == True``
    - ``gulp_calls_executable(skip_non_mock=True)`` if ``gulp_no_mock == True``.
    - ``gulp_doc_notebooks`` if ``gulp_nb_tests != True``

    """
    if config.getoption("gulp_nb_tests_only", False):
        # only run tests marked with GULP_NOTEBOOK_MARKER
        items[:] = [item for item in items if GULP_NOTEBOOK_MARKER in item.keywords]

    test_nbs = config.getoption("gulp_nb_tests", False) or config.getoption(
        "gulp_nb_tests_only", False
    )

    for item in items:  # type: Item

        if (not test_nbs) and (GULP_NOTEBOOK_MARKER in item.keywords):
            item.add_marker(pytest.mark.skip(reason="gulp_nb_tests not specified"))
            continue

        if GULP_CALL_EXEC_MARKER in item.keywords:

            marker = item.get_closest_marker(GULP_CALL_EXEC_MARKER)

            if config.getoption("gulp_skip_exec", False):
                item.add_marker(pytest.mark.skip(reason="gulp_skip_exec specified"))
            elif marker.kwargs.get("skip_non_mock", False) and not use_mock_exec(
                config
            ):
                reason = marker.kwargs.get("reason", "")
                item.add_marker(
                    pytest.mark.skip(
                        reason="gulp_no_mock specified and skip_non_mock=True: {}".format(
                            reason
                        )
                    )
                )


def pytest_report_header(config):
    """Add header information for pytest execution."""
    if use_mock_exec(config):
        header = ["GULP Executables: gulp_mock"]
    else:
        header = ["GULP Executables: gulp"]
    workdir = get_work_directory(config)
    workdir = workdir or "<TEMP>"
    header.append("GULP Work Directory: {}".format(workdir))
    return header


@pytest.fixture(scope="session")
def aiida_environment():
    """Set up an aiida database, profile and for the duration of the tests."""
    # TODO this is required locally for click
    # (see https://click.palletsprojects.com/en/7.x/python3/)
    os.environ["LC_ALL"] = "en_US.UTF-8"
    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope="function")
def db_test_app(aiida_environment, pytestconfig):
    """Create a clean aiida database, profile and temporary work directory for the duration of a test.

    :rtype: aiida_gulp.tests.utils.AiidaTestApp

    """
    if use_mock_exec(pytestconfig):
        print("NB: using mock executable")
        executables = {
            "gulp.single": "gulp_mock",
            "gulp.optimize": "gulp_mock",
            "gulp.fitting": "gulp_mock",
        }
    else:
        executables = {
            "gulp.single": "gulp",
            "gulp.optimize": "gulp",
            "gulp.fitting": "gulp",
        }

    test_workdir = get_work_directory(pytestconfig)
    if test_workdir:
        print("NB: using test workdir: {}".format(test_workdir))
        work_directory = test_workdir
    else:
        work_directory = tempfile.mkdtemp()
    yield AiidaTestApp(work_directory, executables, environment=aiida_environment)
    aiida_environment.reset_db()
    if not test_workdir:
        shutil.rmtree(work_directory)


@pytest.fixture(scope="function")
def get_structure():
    """Return a function that returns a test `aiida.orm.StructureData` instance."""
    return get_test_structure


@pytest.fixture(scope="function")
def get_cif():
    """Return a function that returns a test `aiida.orm.CifData` instance."""  # noqa: D202

    def _get_cif(name):
        from aiida.orm import CifData

        if name == "pyrite":
            with open_resource_binary("cif", "pyrite.cif") as handle:
                return CifData(file=handle)
        raise ValueError(name)

    return _get_cif


@pytest.fixture(scope="function")
def pyrite_potential_lj():
    from aiida.plugins import DataFactory
    from aiida_gulp.potentials.common import INDEX_SEP

    potential_cls = DataFactory("gulp.potential")
    return potential_cls(
        "lj",
        {
            "species": ["Fe core", "S core"],
            "2body": {
                "0" + INDEX_SEP + "0": {"lj_A": 1.0, "lj_B": 1.0, "lj_rmax": 12.0},
                "0" + INDEX_SEP + "1": {"lj_A": 1.0, "lj_B": 1.0, "lj_rmax": 12.0},
                "1" + INDEX_SEP + "1": {"lj_A": 1.0, "lj_B": 1.0, "lj_rmax": 12.0},
            },
        },
    )


@pytest.fixture(scope="function")
def pyrite_potential_reaxff():
    from aiida.plugins import DataFactory
    from aiida_gulp.tests import read_resource_text
    from aiida_gulp.potentials.common import filter_by_species
    from aiida_gulp.potentials.raw_reaxff import read_lammps_format

    data = read_lammps_format(
        read_resource_text("gulp", "potentials", "FeCrOSCH.reaxff").splitlines()
    )
    data = filter_by_species(data, ["Fe core", "S core"])
    return DataFactory("gulp.potential")("reaxff", data)


@pytest.fixture(scope="function")
def pyrite_potential_reaxff_lowtol():
    from aiida.plugins import DataFactory
    from aiida_gulp.tests import read_resource_text
    from aiida_gulp.potentials.common import filter_by_species
    from aiida_gulp.potentials.raw_reaxff import read_lammps_format

    data = read_lammps_format(
        read_resource_text("gulp", "potentials", "FeCrOSCH.reaxff").splitlines()
    )
    data = filter_by_species(data, ["Fe core", "S core"])
    data["global"]["torsionprod"] = 0.001
    return DataFactory("gulp.potential")("reaxff", data)
