"""
Plugin to create a GULP output file from input files created via data nodes
"""
from aiida.orm import DataFactory

from aiida_gulp.calculations.base import BaseCalculation

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')


class SingleCalculation(BaseCalculation):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

    def _init_internal_params(self):  # pylint: disable=useless-super-delegation
        """
        Init internal parameters at class load time
        """
        # reuse base class function
        super(SingleCalculation, self)._init_internal_params()

        self._retrieve_list = ('main.gout', )  # no cif or str

        # parser entry point defined in setup.json
        self._default_parser = 'gulp.single'

    def get_input_keywords(self, parameters):
        """ get list of input keywords

        :type parameters: dict
        :rtype: list of str
        """
        # KeyWord HEADER
        # NB: main output control:
        # 'verb': verbose detail, including energy contributions
        # 'operators': prints out symmetry operations
        # 'prop': print properties, incl bulk/shear modulus, dielectric, refractive
        # 'linmin': print details of minimisation
        # 'comp': print intital/final geometry comparison
        keywords = ['verb', 'operators']

        return keywords

    def get_other_option_lines(self, parameters):
        """ get list of other option lines for .gin

        :type parameters: dict
        :rtype: list of str
        """
        return []

    def get_external_output_lines(self):
        """ get list of external output commands for .gin

        :rtype: list of str
        """
        return []
