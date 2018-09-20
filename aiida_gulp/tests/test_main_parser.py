import os

from jsonextended import edict

from aiida_gulp.parsers.parse_output import parse_output
from aiida_gulp.tests import TEST_DIR


def test_parse_failed():
    path = os.path.join(TEST_DIR, 'output_files', 'empty.gout')
    success, data = parse_output(path, "test_class")

    expected = {'parser_errors': [], 'parser_version': '0.1.0a0', 'errors': ['!! ERROR : input file is empty'],
                'warnings': [], 'energy_units': 'eV', 'parser_class': 'test_class'}

    assert data == expected
    assert not success


def test_parse_opt_reaxff_pyrite():
    path = os.path.join(TEST_DIR, 'output_files', 'opt_reaxff_pyrite.gout')
    success, data = parse_output(path, "test_class")

    print(data)

    expected = {'parser_errors': [], 'parser_version': '0.1.0a0', 'errors': [],
                'energy_contributions': {'Double-Bond Valence Angle Penalty': 0.0, 'Charge Equilibration': -0.25545278,
                                         'Coulomb': -3.11597187, 'Coordination (over)': 17.3593669, 'Conjugation': 0.0,
                                         'Valence Angle': 25.48551722, 'Hydrogen Bond': 0.0,
                                         'Valence Angle Conjugation': 0.0, 'Coordination (under)': 0.0,
                                         'Torsion': 8.40467698, 'Lone-Pair': 2.10108165, 'van der Waals': 3.38859863,
                                         'Bond': -89.68224006}, 'optimised': True, 'warnings': [],
                'initial': {'lattice_energy': {'primitive': -9.51694989}}, 'energy_units': 'eV',
                'parser_class': 'test_class', 'final': {'lattice_energy': {'primitive': -36.31442333}}}

    assert edict.diff(data, expected, np_allclose=True) == {}
    assert success
