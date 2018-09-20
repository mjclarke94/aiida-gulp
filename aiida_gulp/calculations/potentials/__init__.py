import importlib


def get_potential_lines(potential, structure):
    """

    :type potential: dict
    :type structure: aiida.orm.data.structure.StructureData
    :rtype: list of str
    """
    symbols = [site.symbol for site in structure.kinds]
    pair_style = potential['pair_style']
    data = potential['data']

    try:
        potential_module = importlib.import_module('.{}'.format(pair_style), __name__)
    except ImportError:
        raise ImportError('This gulp potential is not implemented: {}'.format(pair_style))

    return potential_module.get_potential_lines(data, symbols)
