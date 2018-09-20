import glob
import os

import pytest

from aiida_gulp.tests import TEST_DIR
import aiida_gulp.tests.utils as tests
from aiida_gulp.parsers.reaxff_convert import read_reaxff_file
import numpy as np


def reaxff_data():
    # pyrite
    cell = [[5.38, 0.000000, 0.000000],
            [0.000000, 5.38, 0.000000],
            [0.000000, 0.000000, 5.38]]

    scaled_positions = [[0.0, 0.0, 0.0],
                        [0.5, 0.0, 0.5],
                        [0.0, 0.5, 0.5],
                        [0.5, 0.5, 0.0],
                        [0.338, 0.338, 0.338],
                        [0.662, 0.662, 0.662],
                        [0.162, 0.662, 0.838],
                        [0.838, 0.338, 0.162],
                        [0.662, 0.838, 0.162],
                        [0.338, 0.162, 0.838],
                        [0.838, 0.162, 0.662],
                        [0.162, 0.838, 0.338]]

    symbols = ['Fe'] * 4 + ['S'] * 8

    struct_dict = {"cell": cell,
                   "symbols": symbols,
                   "scaled_positions": scaled_positions}

    reaxff_path = os.path.join(TEST_DIR, 'input_files', 'FeCrOSCH.reaxff')

    potential_dict = {'pair_style': 'reaxff', 'data': read_reaxff_file(reaxff_path)}

    output_dict = {"units": "real",
                   "energy": -1030.3543,
                   "infiles": ['main.gin'],
                   "warnings": []}

    return struct_dict, potential_dict, output_dict


def setup_calc(workdir, configure, struct_dict, potential_dict, ctype, units):

    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    ParameterData = DataFactory('parameter')

    computer = tests.get_computer(workdir=workdir, configure=configure)

    structure = StructureData(cell=struct_dict["cell"])

    for scaled_position, symbols in zip(struct_dict["scaled_positions"], struct_dict["symbols"]):
        structure.append_atom(position=np.dot(scaled_position, struct_dict["cell"]).tolist(),
                              symbols=symbols)

    potential = ParameterData(dict=potential_dict)

    if ctype == "optimisation":
        # parameters_opt = {
        #     'units': units,
        #     'relax': {
        #         'type': 'iso',
        #         'pressure': 0.0,
        #         'vmax': 0.001,
        #     },
        #     "minimize": {
        #         'style': 'cg',
        #         'energy_tolerance': 1.0e-25,
        #         'force_tolerance': 1.0e-25,
        #         'max_evaluations': 100000,
        #         'max_iterations': 50000}
        # }
        parameters_opt = {
            'title': 'the title',  # optional
            'units': units,
            'relax': {
                'type': 'conp',  # required: one of conp conv cellonly
                'pressure': 0.0  # optional
            },
            "minimize": {
                'style': 'cg',  # required: one of 'nr', 'cg' or 'dfp' (Newton-Raphson with DFP Hessian updater)
                'max_iterations': 50000  # optional
            },
        }
        plugin_name = 'gulp.optimize'

    parameters = ParameterData(dict=parameters_opt)

    code = tests.get_code(computer, plugin_name)
    code.store()

    calc = code.new_calc()
    calc.set_withmpi(False)
    calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 1})

    calc.label = "test lammps calculation"
    calc.description = "A much longer description"
    calc.use_structure(structure)
    calc.use_potential(potential)

    calc.use_parameters(parameters)

    input_dict = {
        "options": {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1
            },
            "withmpi": False,
            "max_wallclock_seconds": 60
        },
        "structure": structure,
        "potential": potential,
        "parameters": parameters,
        "code": code
    }

    return calc, input_dict


@pytest.mark.parametrize('data_func', [
    reaxff_data,
])
def test_opt_submission(new_database, new_workdir, data_func):
    struct_dict, potential_dict, output_dict = data_func()

    calc, input_dict = setup_calc(new_workdir, False,
                                  struct_dict, potential_dict, 'optimisation',
                                  output_dict['units'])

    from aiida.common.folders import SandboxFolder

    # output input files and scripts to temporary folder
    with SandboxFolder() as folder:
        subfolder, script_filename = calc.submit_test(folder=folder)
        print("inputs created successfully at {}".format(subfolder.abspath))
        print([
            os.path.basename(p)
            for p in glob.glob(os.path.join(subfolder.abspath, "*"))
        ])
        for infile in output_dict['infiles']:
            assert subfolder.isfile(infile)
            print('---')
            print(infile)
            print('---')
            with subfolder.open(infile) as f:
                print(f.read())
