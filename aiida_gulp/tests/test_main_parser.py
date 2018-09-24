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
            'Charge Equilibration': -0.35733251,
            'Coulomb': -2.95800482,
            'Coordination (over)': 12.16296392,
            'Conjugation': 0.0,
            'Valence Angle': 13.80015008,
            'Hydrogen Bond': 0.0,
            'Valence Angle Conjugation': 0.0,
            'Coordination (under)': 0.0,
            'Torsion': 0.19158951,
            'Lone-Pair': 1.21399426,
            'van der Waals': 5.95617879,
            'Bond': -77.39551881
        },
        'optimised': True,
        'warnings': [],
        'energy': -47.38597959,
        'energy_units': 'eV',
        'energy_initial': -42.20546311,
        'parser_class': 'test_class'
    }

    assert edict.diff(data, expected, np_allclose=True) == {}
    assert success
