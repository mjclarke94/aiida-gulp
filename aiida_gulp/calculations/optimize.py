"""
Plugin to create a GULP output file from input files created via data nodes
"""
from aiida.orm import DataFactory

from aiida_gulp.calculations.base import BaseCalculation
from aiida_gulp.common.units import get_pressure
from aiida_gulp.validation import validate_with_json

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')


class OptCalculation(BaseCalculation):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

    def _init_internal_params(self):  # pylint: disable=useless-super-delegation
        """
        Init internal parameters at class load time
        """
        # reuse base class function
        super(OptCalculation, self)._init_internal_params()

        # parser entry point defined in setup.json
        self._default_parser = 'gulp.optimize'

    def validate_parameters(self, parameters):
        """

        :type parameters: dict
        :return:
        """
        validate_with_json(parameters, "optimize")

    def get_input_keywords(self, parameters):
        """ get list of input keywords

        :type parameters: dict
        :returns: list of strings
        :rtype: list(str)
        """
        # KeyWord HEADER
        # NB: main output control:
        # 'verb': verbose detail, including energy contributions
        # 'operators': prints out symmetry operations
        # 'prop': print properties, incl bulk/shear modulus, dielectric, refractive
        # 'linmin': print details of minimisation
        # 'comp': print intital/final geometry comparison
        keywords = ['optimise', 'verb', parameters['relax']['type']]
        if parameters['minimize']['style'] != 'nr':
            keywords.append(parameters['minimize']['style'])

        # TODO switch between symmetric and non-symmetric (use settings input node like CRYSTAL)
        # if not params.get('symmetry', True):
        #     # Switches off symmetry after generating unit cell
        #     keywords.append('nosymmetry')
        #  	'full' keyword causes the nosymmetry keyword to produce the full, instead of the primitive, unit cell.

        return keywords

    def get_other_option_lines(self, parameters):
        """ get list of other option lines for .gin

        :type parameters: dict
        :returns: list of strings
        :rtype: list(str)
        """
        lines = []

        # TODO set energy units: in eV by default, or can use keywords: kcal, kjmol

        if parameters['relax'].get('pressure', False):
            pressure, punits = get_pressure(parameters['relax']['pressure'],
                                            parameters['units'])
            lines.append('pressure {0:.4f} {1}'.format(pressure, punits))
        # NB: Causes energy to be replaced by enthalpy in calculations.

        # maximum number of optimisation steps (default 1000)
        if 'max_iterations' in parameters['minimize']:
            lines.append('maxcyc opt {}\n'.format(
                parameters['minimize']['max_iterations']))

        # TODO how do these compare to tolerances from LAMMPS?
        # maximum parameter tolerance (default 0.00001)
        # xtol opt 0.00001
        # maximum function tolerance (default 0.00001)
        # ftol opt 0.00001
        # maximum gradient tolerance (default 0.001)
        # gtol opt 0.001
        # NB: ftol should always be less than gtol
        # maximum allowed individual gradient component (default 0.01)
        # gmax opt 0.01
        return lines
