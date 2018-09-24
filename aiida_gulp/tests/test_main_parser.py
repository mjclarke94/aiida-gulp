import os
from jsonextended import edict

from aiida_gulp import __version__
from aiida_gulp.parsers.parse_output import parse_output
from aiida_gulp.tests import TEST_DIR


def test_parse_failed():
    path = os.path.join(TEST_DIR, 'output_files', 'empty.gout')
    success, data = parse_output(path, "test_class")

    expected = {
        'parser_errors': ["expected 'initial' data"],
        'parser_version': __version__,
        'errors': ['!! ERROR : input file is empty'],
        'warnings': [],
        'energy_units': 'eV',
        'parser_class': 'test_class'
    }

    assert data == expected
    assert not success


def test_parse_opt_reaxff_pyrite():
    path = os.path.join(TEST_DIR, 'output_files', 'opt_reaxff_pyrite.gout')
    success, data = parse_output(path, "test_class", final=True)

    print(data)

    expected = {
        'parser_errors': [],
        'parser_version': __version__,
        'errors': [],
        'energy_contributions': {
            'Double-Bond Valence Angle Penalty': 0.0,
            'Charge Equilibration': -0.26861672,
            'Coulomb': -3.09567064,
            'Coordination (over)': 9.9335806,
            'Conjugation': 0.0,
            'Valence Angle': 14.85816318,
            'Hydrogen Bond': 0.0,
            'Valence Angle Conjugation': 0.0,
            'Coordination (under)': 1.1e-07,
            'Torsion': 0.79757591,
            'Lone-Pair': 1.21245733,
            'van der Waals': 3.23561148,
            'Bond': -70.24055778
        },
        'optimised': True,
        'warnings': [],
        'energy_units': 'eV',
        'parser_class': 'test_class',
        'energy_initial': -42.20546311,
        'energy': -43.56745651
    }

    assert edict.diff(data, expected, np_allclose=True) == {}
    assert success
