"""
Plugin to create a GULP output file from input files created via data nodes
"""
import os
from abc import abstractmethod

import numpy as np

from aiida.common.exceptions import InputValidationError
from aiida.common.utils import classproperty
from aiida.orm import JobCalculation
from aiida.orm import DataFactory, Data
from aiida.common.datastructures import (CalcInfo, CodeInfo)

from aiida_gulp.calculations.potentials import get_potential_lines
from aiida_gulp.geometry import CRYSTAL_TYPE_MAP
from aiida_gulp.validation import validate_with_json

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
        self._retrieve_list = ('main.gout', 'main.cif')
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
            "symmetry": {
                'valid_types':
                ParameterData,
                'additional_parameter':
                None,
                'linkname':
                'symmetry',
                'docstring':
                "the input parameters to create the symmetry section of .gin file content."
            },
            "structure": {
                'valid_types': StructureData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "structure to use."
            }
        })

        return use_dict

    # pylint: disable=too-many-arguments
    def _create_input_files(self, tempfolder, parameters, potential, instruct,
                            symmetry):
        """

        :param tempfolder:
        :param parameters: dict or None
        :param potential: dict
        :param instruct: aiida.orm.data.structure.StructureData
        :param symmetry: dict or None
        :return:
        """
        if not parameters:
            parameters = {}
        else:
            parameters = parameters.get_dict()
            self.validate_parameters(parameters)
        if not symmetry:
            symmetry = {}
        else:
            symmetry = symmetry.get_dict()
            validate_with_json(symmetry, 'symmetry')

        filecontent = ""

        keywords = self.get_input_keywords(parameters)

        filecontent += " ".join(keywords) + '\n'

        # TITLE
        if 'title' in parameters:
            filecontent += '\ntitle\n{}\nend\n'.format(parameters['title'])

        # GEOMETRY
        filecontent += "\n# Geometry\n"
        filecontent += "\n".join(self.get_geometry_lines(instruct, symmetry))

        # FORCE FIELD
        filecontent += "\n\n# Force Field\n"
        filecontent += "\n".join(
            self.get_ffield_lines(potential.get_dict(), instruct))

        # OTHER OPTIONS
        filecontent += "\n\n# Other Options\n"
        filecontent += "\n".join(self.get_other_option_lines(parameters))

        # EXTERNAL OUTPUT OPTIONS
        filecontent += "\n\n# External Outputs\n"
        filecontent += "\n".join(self.get_external_output_lines())

        filecontent += "\n"
        filecontent += "#---END---"

        with open(tempfolder.get_abs_path(self._DEFAULT_INPUT_FILE), 'w') as f:
            f.write(filecontent)

    def validate_parameters(self, parameters):
        raise NotImplementedError

    @abstractmethod
    def get_input_keywords(self, parameters):
        """ get list of input keywords for .gin

        :type parameters: dict
        :returns: list of strings
        :rtype: list(str)
        """
        raise NotImplementedError

    def get_geometry_lines(self, instruct, symmetry):
        """ get list of geometry lines for .gin

        :type instruct: aiida.orm.data.structure.StructureData
        :returns: list of strings
        :rtype: list(str)
        """
        lines = ['name main-geometry']

        ops = symmetry.get('operations', [])
        # remove identity matrix
        ops = [
            op for op in ops
            if not np.allclose(op, [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
        ]
        equiv_atoms = symmetry.get('equivalent',
                                   list(range(len(instruct.sites))))
        crystal_type = symmetry.get('crystal_type', None)

        if ops and len(equiv_atoms) != len(instruct.sites):
            raise AssertionError(
                'The length of equivalent atoms is not equal to the number of sites'
            )

        if all(instruct.pbc):
            lines.append('vectors')
            for vector in instruct.cell:
                lines.append("{0:.6f} {1:.6f} {2:.6f} ".format(*vector))

            lines.append('cartesian')
            all_equiv = []
            for site, equiv in zip(instruct.sites, equiv_atoms):

                # only add in-equivalent atoms
                if equiv in all_equiv:
                    continue
                all_equiv.append(equiv)

                kind = instruct.get_kind(site.kind_name)
                lines.append("{0} core {1:.6f} {2:.6f} {3:.6f}".format(
                    kind.symbol, *site.position))

            if crystal_type:
                if isinstance(crystal_type, int):
                    crystal_type = CRYSTAL_TYPE_MAP[crystal_type]
                assert crystal_type in [
                    "triclinic", "monoclinic", "orthorhombic", "tetragonal",
                    "hexagonal", "rhombohedral", "cubic"
                ]
                lines.append("symmetry_cell {}".format(crystal_type))

            for op in ops:
                lines.append('symmetry_operator')
                lines.append("{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}".format(
                    op[0], op[3], op[6], op[9]))
                lines.append("{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}".format(
                    op[1], op[4], op[7], op[10]))
                lines.append("{0:8.5f} {1:8.5f} {2:8.5f} {3:8.5f}".format(
                    op[2], op[5], op[8], op[11]))
        else:
            # TODO For 2D use svectors and sfractional, can you specify symmetry operations?
            raise NotImplementedError('periodicity lower than 3')

        return lines

    def get_ffield_lines(self, potential, structure):
        """ get list of force field lines for .gin

        :type potential: dict
        :type structure: aiida.orm.data.structure.StructureData
        :returns: list of strings
        :rtype: list(str)
        """
        return get_potential_lines(potential, structure)

    @abstractmethod
    def get_other_option_lines(self, parameters):
        """ get list of other option lines for .gin

        :type parameters: dict
        :returns: list of strings
        :rtype: list(str)
        """
        raise NotImplementedError

    def get_external_output_lines(self):
        """ get list of external output commands for .gin

        :returns: list of strings
        :rtype: list(str)
        """
        return [
            'output cif {}'.format(
                os.path.splitext(self._DEFAULT_CIF_FILE)[0]),
            # 'output str {}'.format(
            #     os.path.splitext(self._DEFAULT_STR_FILE)[0]),
        ]
        # 'output str <filename_no_ext>' outputs CRYSTAL98 .gui file

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
        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this "
                                       "calculation")

        potential = self._pop_input(inputdict, 'potential', ParameterData)
        instruct = self._pop_input(inputdict, 'structure', StructureData)
        parameters = self._pop_input(
            inputdict, 'parameters', ParameterData, allow_none=True)
        symmetry = self._pop_input(
            inputdict, 'symmetry', Data, allow_none=True)

        if inputdict:
            raise InputValidationError(
                "Unknown additional inputs: {}".format(inputdict))

        self._create_input_files(tempfolder, parameters, potential, instruct,
                                 symmetry)

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

    def _pop_input(self, inputdict, name, ntype, allow_none=False):
        try:
            innode = inputdict.pop(self.get_linkname(name))
        except KeyError:
            if not allow_none:
                raise InputValidationError("Missing {0}".format(name))
            else:
                return None
        if not isinstance(innode, ntype):
            raise InputValidationError("{0} not of type {1}".format(
                name, ntype))
        return innode
