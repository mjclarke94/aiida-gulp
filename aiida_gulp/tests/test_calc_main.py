import glob
import os

import pytest
import sys
from aiida_gulp.common.compatibility import aiida_version, cmp_version, run_get_node

from aiida_gulp.tests import TEST_DIR
import aiida_gulp.tests.utils as tests
from aiida_gulp.parsers.reaxff_convert import read_reaxff_file
import numpy as np


def reaxff_data():
    # pyrite
    cell = [[5.38, 0.000000, 0.000000], [0.000000, 5.38, 0.000000],
            [0.000000, 0.000000, 5.38]]

    scaled_positions = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.5], [
        0.5, 0.5, 0.0
    ], [0.338, 0.338, 0.338], [0.662, 0.662, 0.662], [0.162, 0.662, 0.838],
                        [0.838, 0.338, 0.162], [0.662, 0.838, 0.162],
                        [0.338, 0.162, 0.838], [0.838, 0.162,
                                                0.662], [0.162, 0.838, 0.338]]

    symbols = ['Fe'] * 4 + ['S'] * 8

    struct_dict = {
        "cell": cell,
        "symbols": symbols,
        "scaled_positions": scaled_positions
    }

    reaxff_path = os.path.join(
        TEST_DIR,
        'input_files',
        'FeCrOSCH.reaxff',
    )

    potential_dict = {
        'pair_style': 'reaxff',
        'data': read_reaxff_file(reaxff_path)
    }

    output_dict = {
        "units": "real",
        # in lammps -1027.9739 kcal/mole = -4301.0427976 kJ/mole = -44.577166 eV
        # in gulp, with standard tolerances, -42.20546311 eV
        # with a lower torsioprod tolerance (0.001), -44.57768894 eV
        "initial_energy": -42.20546311,
        "final_energy": -43.56745651,
        "infiles": ['main.gin'],
        "warnings": []
    }

    return struct_dict, potential_dict, output_dict


def setup_calc(workdir, configure, struct_dict, potential_dict, ctype, units):

    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    ParameterData = DataFactory('parameter')

    computer = tests.get_computer(workdir=workdir, configure=configure)

    structure = StructureData(cell=struct_dict["cell"])

    for scaled_position, symbols in zip(struct_dict["scaled_positions"],
                                        struct_dict["symbols"]):
        structure.append_atom(
            position=np.dot(scaled_position, struct_dict["cell"]).tolist(),
            symbols=symbols)

    potential = ParameterData(dict=potential_dict)

    if ctype == "single":
        parameters_opt = {
            'title': 'the title',  # optional
        }
        plugin_name = 'gulp.single'
    elif ctype == "optimisation":
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
                'style':
                'cg',  # required: one of 'nr', 'cg' or 'dfp' (Newton-Raphson with DFP Hessian updater)
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
def test_single_submission(new_database, new_workdir, data_func):
    struct_dict, potential_dict, output_dict = data_func()

    calc, input_dict = setup_calc(new_workdir, False, struct_dict,
                                  potential_dict, 'single',
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


@pytest.mark.parametrize('data_func', [
    reaxff_data,
])
def test_opt_submission(new_database, new_workdir, data_func):
    struct_dict, potential_dict, output_dict = data_func()

    calc, input_dict = setup_calc(new_workdir, False, struct_dict,
                                  potential_dict, 'optimisation',
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


@pytest.mark.lammps_call
@pytest.mark.timeout(120)
@pytest.mark.skipif(
    aiida_version() < cmp_version('1.0.0a1') and tests.is_sqla_backend(),
    reason='Error in obtaining authinfo for computer configuration')
@pytest.mark.parametrize('data_func', [
    reaxff_data,
])
def test_single_process(new_database_with_daemon, new_workdir, data_func):
    struct_dict, potential_dict, output_dict = data_func()

    calc, input_dict = setup_calc(new_workdir, True, struct_dict,
                                  potential_dict, 'single',
                                  output_dict['units'])

    process = calc.process()

    calcnode = run_get_node(process, input_dict)

    sys.stdout.write(tests.get_calc_log(calcnode))

    print(calcnode.get_inputs_dict())
    assert set(calcnode.get_inputs_dict().keys()).issuperset(
        ['parameters', 'structure', 'potential'])

    print(calcnode.get_outputs_dict())
    assert set(calcnode.get_outputs_dict().keys()).issuperset(
        ['output_parameters'])

    from aiida.common.datastructures import calc_states
    assert calcnode.get_state() == calc_states.FINISHED

    pdict = calcnode.out.output_parameters.get_dict()
    print(pdict)
    assert set(pdict.keys()).issuperset([
        'energy', 'warnings', 'energy_units', 'parser_class', 'parser_version'
    ])
    assert pdict['warnings'] == output_dict["warnings"]
    assert pdict['energy'] == pytest.approx(output_dict['initial_energy'])


@pytest.mark.lammps_call
@pytest.mark.timeout(120)
@pytest.mark.skipif(
    aiida_version() < cmp_version('1.0.0a1') and tests.is_sqla_backend(),
    reason='Error in obtaining authinfo for computer configuration')
@pytest.mark.parametrize('data_func', [
    reaxff_data,
])
def test_opt_process(new_database_with_daemon, new_workdir, data_func):
    struct_dict, potential_dict, output_dict = data_func()

    calc, input_dict = setup_calc(new_workdir, True, struct_dict,
                                  potential_dict, 'optimisation',
                                  output_dict['units'])

    process = calc.process()

    calcnode = run_get_node(process, input_dict)

    sys.stdout.write(tests.get_calc_log(calcnode))

    print(calcnode.get_inputs_dict())
    assert set(calcnode.get_inputs_dict().keys()).issuperset(
        ['parameters', 'structure', 'potential'])

    print(calcnode.get_outputs_dict())
    assert set(calcnode.get_outputs_dict().keys()).issuperset(
        ['output_parameters', 'output_structure'])

    from aiida.common.datastructures import calc_states
    assert calcnode.get_state() == calc_states.FINISHED

    pdict = calcnode.out.output_parameters.get_dict()
    print(pdict)
    assert set(pdict.keys()).issuperset([
        'energy', 'warnings', 'energy_units', 'parser_class', 'parser_version'
    ])
    assert pdict['warnings'] == output_dict["warnings"]
    assert pdict['energy_initial'] == pytest.approx(
        output_dict['initial_energy'])
    assert pdict['energy'] == pytest.approx(output_dict['final_energy'])
