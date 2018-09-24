"""
A parser to read output from a standard GULP run
"""
from aiida.orm import CalculationFactory
from aiida.orm import DataFactory
from aiida.parsers.exceptions import OutputParsingError
from aiida.parsers.parser import Parser
from aiida.common.datastructures import calc_states

from aiida_gulp.parsers.parse_output import parse_output


class OptParser(Parser):
    """
    Parser class for parsing output of a standard GULP run
    """

    def __init__(self, calculation):
        """
        Initialize Parser instance
        """
        # check for valid input
        if not isinstance(calculation, CalculationFactory('gulp.optimize')):
            raise OutputParsingError(
                "Can only parse gulp.optimize calculation")

        super(OptParser, self).__init__(calculation)

    # pylint: disable=protected-access
    def check_state(self):
        """Log an error if the calculation being parsed is not in PARSING state."""
        if self._calc.get_state() != calc_states.PARSING:
            self.logger.error('Calculation not in parsing state')

    # pylint: disable=protected-access
    def get_folder(self, retrieved):
        """Convenient access to the retrieved folder."""
        try:
            out_folder = retrieved[self._calc._get_linkname_retrieved()]
            return out_folder
        except KeyError:
            self.logger.error('No retrieved folder found')
            return None

    @classmethod
    def get_linkname_outstructure(cls):
        """
        Returns the name of the link to the output_structure
        Node exists if positions or cell changed.
        """
        return 'output_structure'

    # pylint: disable=too-many-locals
    def parse_with_retrieved(self, retrieved):
        """
        Parse outputs, store results in database.

        :param retrieved: a dictionary of retrieved nodes, where
          the key is the link name
        :returns: a tuple with two values ``(bool, node_list)``,
          where:

          * ``bool``: variable to tell if the parsing succeeded
          * ``node_list``: list of new nodes to be stored in the db
            (as a list of tuples ``(link_name, node)``)
        """
        CifData = DataFactory('cif')
        ParameterData = DataFactory('parameter')

        node_list = []
        successful = True

        # check calc in parsing state
        self.check_state()

        # Check that the retrieved folder is there
        out_folder = self.get_folder(retrieved)
        if not out_folder:
            return False, ()

        list_of_files = out_folder.get_folder_list()

        # Check that the required files are present
        mainout_file = self._calc._DEFAULT_OUTPUT_FILE  # pylint: disable=protected-access
        outcif_file = self._calc._DEFAULT_CIF_FILE  # pylint: disable=protected-access

        if mainout_file not in list_of_files:
            self.logger.error(
                "The standard output file '{}' was not found but is required".
                format(mainout_file))
            return False, ()

        # parse the output file and add nodes
        self.logger.info("parsing main out file")
        psuccess, outparams = parse_output(
            out_folder.get_abs_path(mainout_file),
            parser_class=self.__class__.__name__,
            final=True)

        if not psuccess:
            successful = False

        perrors = outparams["errors"]

        if perrors:
            self.logger.warning(
                "the parser raised the following errors:\n{}".format(
                    "\n\t".join(perrors)))

        if outcif_file not in list_of_files:
            pass
            # msg = "The output cif file '{}' was not found but is required".format(outcif_file)
            # self.logger.error(msg)
            # outparams['parser_errors'].append(msg)
            # successful = False
        else:
            cif = CifData(file=out_folder.get_abs_path(outcif_file))
            structure = cif._get_aiida_structure(primitive_cell=False)
            node_list.append((self.get_linkname_outstructure(), structure))

        node_list.insert(
            0, (self.get_linkname_outparams(), ParameterData(dict=outparams)))

        return successful, node_list
