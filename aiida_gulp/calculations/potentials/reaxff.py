"""create reaxff data"""
from aiida_gulp.parsers.reaxff_convert import write_gulp


def get_potential_lines(data, symbols):
    outstr = write_gulp(data, symbols)
    return outstr.splitlines()