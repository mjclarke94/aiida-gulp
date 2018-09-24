"""
Plugin to create a GULP output file from input files created via data nodes
"""
import os
from abc import abstractmethod

from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty
from aiida.orm import JobCalculation
from aiida.orm import DataFactory
from aiida.common.datastructures import (CalcInfo, CodeInfo)

from aiida_gulp.calculations.potentials import get_potential_lines

StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')


class BaseCalculation(JobCalculation):
    """
    AiiDA calculation plugin wrapping the runcry17 executable.

    """

    def _init_internal_params(self):  # pylint: disable=useless-super-delegation
        """
        Init internal parameters at class load time
        """
        # reuse base class function
        super(BaseCalculation, self)._init_internal_params()

        # default input and output files
        self._DEFAULT_INPUT_FILE = 'main.gin'
        self._DEFAULT_OUTPUT_FILE = 'main.gout'
        self._DEFAULT_CIF_FILE = 'main.cif'
        self._DEFAULT_STR_FILE = 'main.str'
        self._retrieve_list = ('main.gout', 'main.cif', 'main.str')
        self._retrieve_temporary_list = ()

        # parser entry point defined in setup.json
        self._default_parser = None

    @classproperty
    def _use_methods(cls):
        """
        Add use_* methods for calculations.

        Code below enables the usage
        my_calculation.use_parameters(my_parameters)

        """
        use_dict = JobCalculation._use_methods

        use_dict.update({
            "parameters": {
                'valid_types':
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'parameters',
                'docstring':
                "the input parameters to create the .gin file content."
            },
            "potential": {
                'valid_types':
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'potential',
                'docstring':
                "the input parameters to create the potential section of .gin file content."
            },
            "structure": {
                'valid_types': StructureData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "structure to use."
            }
        })

        return use_dict

    def _create_input_files(self, tempfolder, parameters, potential, instruct):
        """

        :param parameters:
        :param potential:
        :param instruct:
        :return:
        """
        filecontent = ""

        keywords = self.get_input_keywords(parameters)

        filecontent += " ".join(keywords) + '\n'

        # TITLE
        if 'title' in parameters:
            filecontent += '\ntitle\n{}\nend\n'.format(parameters['title'])

        # GEOMETRY
        filecontent += "\n# Geometry\n"
        filecontent += "\n".join(self.get_geometry_lines(instruct))

        # FORCE FIELD
        filecontent += "\n\n# Force Field\n"
        filecontent += "\n".join(self.get_ffield_lines(potential, instruct))

        # OTHER OPTIONS
        filecontent += "\n\n# Other Options\n"
        filecontent += "\n".join(self.get_other_option_lines(parameters))

        # EXTERNAL OUTPUT OPTIONS
        filecontent += "\n\n# External Outputs\n"
        filecontent += "\n".join(self.get_external_output_lines())

        with open(tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE), 'w') as f:
            f.write(filecontent)

    @abstractmethod
    def get_input_keywords(self, parameters):
        """ get list of input keywords for .gin

        :type parameters: dict
        :rtype: list of str
        """
        raise NotImplementedError

    def get_geometry_lines(self, instruct):
        """ get list of geometry lines for .gin

        :type instruct: aiida.orm.data.structure.StructureData
        :rtype: list of str
        """
        lines = ['name main-geometry']

        if all(instruct.pbc):
            lines.append('vectors')
            for vector in instruct.cell:
                lines.append("{0:.6f} {1:.6f} {2:.6f} ".format(*vector))

            lines.append('cartesian')
            for site in instruct.sites:
                kind = instruct.get_kind(site.kind_name)
                x, y, z = site.position
                lines.append("{0} core {1:.6f} {2:.6f} {3:.6f}".format(
                    kind.symbol, x, y, z))
        else:
            # For 2D use svectors and sfractional
            raise NotImplementedError('periodicity lower than 3')

        return lines

    def get_ffield_lines(self, potential, structure):
        """ get list of force field lines for .gin

        :type potential: dict
        :type structure: aiida.orm.data.structure.StructureData
        :rtype: list of str
        """
        return get_potential_lines(potential, structure)

    @abstractmethod
    def get_other_option_lines(self, parameters):
        """ get list of other option lines for .gin

        :type parameters: dict
        :rtype: list of str
        """
        raise NotImplementedError

    def get_external_output_lines(self):
        """ get list of external output commands for .gin

        :rtype: list of str
        """
        return [
            'output cif {}'.format(
                os.path.splitext(self._DEFAULT_CIF_FILE)[0]),
            'output str {}'.format(
                os.path.splitext(self._DEFAULT_STR_FILE)[0]),
        ]
        # 'output str <filename_no_ext>' would output CRYSTAL .gui file

    def _prepare_for_submission(self, tempfolder, inputdict):
        """
        Create input files.

            :param tempfolder: aiida.common.folders.Folder subclass where
                the plugin should put all its files.
            :param inputdict: dictionary of the input nodes as they would
                be returned by get_inputs_dict

        See https://aiida-core.readthedocs.io/en/latest/
        developer_guide/devel_tutorial/code_plugin_qe.html#step-3-prepare-a-text-input
        for a description of its function and inputs
        """
        # read inputs
        # we expect "code", "parameters", "structure" and "potential"
        # "settings" is optional

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")

        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("Missing parameters")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters not of type ParameterData")

        try:
            potential = inputdict.pop(self.get_linkname('potential'))
        except KeyError:
            raise InputValidationError("Missing potential")
        if not isinstance(potential, ParameterData):
            raise InputValidationError("potential not of type ParameterData")

        try:
            instruct = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("Missing structure")
        if not isinstance(instruct, StructureData):
            raise InputValidationError("structure not of type StructureData")

        if inputdict:
            raise InputValidationError(
                "Unknown additional inputs: {}".format(inputdict))

        self._create_input_files(tempfolder, parameters.get_dict(),
                                 potential.get_dict(), instruct)

        # Prepare CodeInfo object for aiida, describes how a code has to be executed
        codeinfo = CodeInfo()
        codeinfo.code_uuid = code.uuid
        codeinfo.cmdline_params = [
            os.path.splitext(self._DEFAULT_INPUT_FILE)[0]
        ]
        # codeinfo.stdout_name =
        codeinfo.withmpi = self.get_withmpi()

        # Prepare CalcInfo object for aiida
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.retrieve_list = list(self._retrieve_list)
        calcinfo.retrieve_temporary_list = list(self._retrieve_temporary_list)

        return calcinfo
