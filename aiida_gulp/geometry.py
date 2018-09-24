import numpy as np
from aiida_gulp.validation import validate_with_json

CRYSTAL_TYPE_MAP = {
    1: 'triclinic',
    2: 'monoclinic',
    3: 'orthorhombic',
    4: 'tetragonal',
    5: 'hexagonal',
    6: 'cubic'
}

CRYSTAL_TYPE_NUM_MAP = {
    'triclinic': 1,
    'monoclinic': 2,
    'orthorhombic': 3,
    'tetragonal': 4,
    'hexagonal': 5,
    'rhombohedral': 5,
    'triganol': 5,
    'cubic': 6
}

ATOMIC_NUM2SYMBOL = {
    1: 'H',
    2: 'He',
    3: 'Li',
    4: 'Be',
    5: 'B',
    6: 'C',
    7: 'N',
    8: 'O',
    9: 'F',
    10: 'Ne',
    11: 'Na',
    12: 'Mg',
    13: 'Al',
    14: 'Si',
    15: 'P',
    16: 'S',
    17: 'Cl',
    18: 'Ar',
    19: 'k',
    20: 'Ca',
    21: 'Sc',
    22: 'Ti',
    23: 'v',
    24: 'Cr',
    25: 'Mn',
    26: 'Fe',
    27: 'Co',
    28: 'Ni',
    29: 'Cu',
    30: 'Zn',
    31: 'Ga',
    32: 'Ge',
    33: 'As',
    34: 'Se',
    35: 'Br',
    36: 'Kr',
    37: 'Rb',
    38: 'Sr',
    39: 'Y',
    40: 'Zr',
    41: 'Nb',
    42: 'Mo',
    43: 'Tc',
    45: 'Ru',
    46: 'Pd',
    47: 'Ag',
    48: 'Cd',
    49: 'In',
    50: 'Sn',
    51: 'Sb',
    52: 'Te',
    53: 'I',
    54: 'Xe',
    55: 'Cs',
    56: 'Ba',
    57: 'La',
    72: 'Hf',
    73: 'Ta',
    74: 'W',
    75: 'Re',
    76: 'Os',
    77: 'Ir',
    78: 'Pt',
    79: 'Au',
    80: 'Hg',
    81: 'Tl',
    82: 'Pb',
    83: 'Bi',
    84: 'Po',
    85: 'At',
    86: 'Rn',
    87: 'Fr',
    88: 'Ra',
    89: 'Ac',
    104: 'Rf',
    105: 'Db',
    106: 'Sg',
    107: 'Bh',
    108: 'Hs',
    109: 'Mt'
}

ATOMIC_SYMBOL2NUM = {v: k for k, v in ATOMIC_NUM2SYMBOL.items()}


def structdict_to_ase(structdict):
    """convert struct dict to ase.Atoms

    :param structdict: dict containing 'lattice', 'atomic_numbers', 'pbc', 'ccoords', 'equivalent'
    :rtype: ase.Atoms
    """
    import ase
    atoms = ase.Atoms(
        cell=structdict["lattice"],
        numbers=structdict["atomic_numbers"],
        pbc=structdict["pbc"],
        positions=structdict["ccoords"],
        tags=structdict["equivalent"])
    return atoms


def ase_to_structdict(atoms):
    """convert ase.Atoms to struct dict

    :type atoms: ase.Atoms
    :return structdict: dict containing 'lattice', 'atomic_numbers', 'pbc', 'ccoords', 'equivalent'
    :type structdict: dict
    """
    structdict = {
        "lattice": atoms.cell.tolist(),
        "ccoords": atoms.positions.tolist(),
        "atomic_numbers": atoms.get_atomic_numbers().tolist(),
        "pbc": atoms.pbc.tolist(),
        "equivalent": atoms.get_tags().tolist()
    }
    return structdict


def structure_to_dict(structure):
    """create a dictionary of structure properties per atom

    :param structure: the input structure
    :type structure: aiida.orm.data.structure.StructureData
    :return: dictionary containing; lattice, atomic_numbers, ccoords, pbc, kinds, equivalent
    :rtype: dict

    """
    from aiida.common.exceptions import InputValidationError

    for kind in structure.kinds:
        if kind.is_alloy():
            raise InputValidationError(
                "Kind '{}' is an alloy. This is not allowed for CRYSTAL input structures."
                "".format(kind.name))
        if kind.has_vacancies():
            raise InputValidationError(
                "Kind '{}' has vacancies. This is not allowed for CRYSTAL input structures."
                "".format(kind.name))

    kindname_symbol_map = {
        kind.name: kind.symbols[0]
        for kind in structure.kinds
    }
    kindname_id_map = {kind.name: i for i, kind in enumerate(structure.kinds)}
    id_kind_map = {i: kind for i, kind in enumerate(structure.kinds)}
    kind_names = [site.kind_name for site in structure.sites]
    symbols = [kindname_symbol_map[name] for name in kind_names]
    equivalent = [kindname_id_map[name] for name in kind_names]
    kinds = [id_kind_map[e] for e in equivalent]

    sdata = {
        "lattice": structure.cell,
        "atomic_numbers": [ATOMIC_SYMBOL2NUM[sym] for sym in symbols],
        "ccoords": [site.position for site in structure.sites],
        "pbc": structure.pbc,
        "equivalent": equivalent,
        "kinds": kinds,
    }

    return sdata


def dict_to_structure(structdict, logger=None):
    """create a dictionary of structure properties per atom

    :param: dictionary containing; 'lattice', 'atomic_numbers' (or 'symbols'), 'ccoords', 'pbc', 'kinds', 'equivalent'
    :type structdict: dict
    :param logger: a logger with a `warning` method
    :return structure: the input structure
    :rtype structure: aiida.orm.data.structure.StructureData

    """
    from aiida.orm import DataFactory
    StructureData = DataFactory('structure')
    struct = StructureData(cell=structdict['lattice'])
    struct.set_pbc(structdict["pbc"])
    atom_kinds = structdict.get("kinds", None)

    if atom_kinds is None:
        if logger:
            logger.warning("no 'kinds' available, creating new kinds")
        symbols = structdict.get("symbols", None)
        if symbols is None:
            symbols = [
                ATOMIC_NUM2SYMBOL[anum]
                for anum in structdict["atomic_numbers"]
            ]

        if len(symbols) != len(structdict['ccoords']):
            raise AssertionError(
                "the length of ccoords and atomic_numbers/symbols must be the same"
            )
        for symbol, ccoord in zip(symbols, structdict['ccoords']):
            struct.append_atom(position=ccoord, symbols=symbol)
    else:
        if len(atom_kinds) != len(structdict['ccoords']):
            raise AssertionError(
                "the length of ccoords and atom_kinds must be the same")

        from aiida.orm.data.structure import Site, Kind
        for kind, ccoord in zip(atom_kinds, structdict['ccoords']):
            if not isinstance(kind, Kind):
                kind = Kind(raw=kind)
            if kind.name not in struct.get_site_kindnames():
                struct.append_kind(kind)
            struct.append_site(Site(position=ccoord, kind_name=kind.name))

    return struct


def get_crystal_system(sg_number, as_number=False):
    """Get the crystal system for the structure, e.g.,
    (triclinic, orthorhombic, cubic, etc.) from the space group number

    :param sg_number: the spacegroup number
    :param as_number: return the system as a number (recognized by CRYSTAL) or a str
    :return: Crystal system for structure or None if system cannot be detected.
    """
    f = lambda i, j: i <= sg_number <= j
    cs = {
        "triclinic": (1, 2),
        "monoclinic": (3, 15),
        "orthorhombic": (16, 74),
        "tetragonal": (75, 142),
        "trigonal": (143, 167),
        "hexagonal": (168, 194),
        "cubic": (195, 230)
    }

    crystal_system = None

    for k, v in cs.items():
        if f(*v):
            crystal_system = k
            break

    if crystal_system is None:
        raise ValueError(
            "could not find crystal system of space group number: {}".format(
                sg_number))

    if as_number:
        crystal_system = CRYSTAL_TYPE_NUM_MAP[crystal_system]

    return crystal_system


def get_lattice_type(sg_number):
    """Get the lattice for the structure, e.g., (triclinic,
    orthorhombic, cubic, etc.).This is the same than the
    crystal system with the exception of the hexagonal/rhombohedral
    lattice

    :param sg_number: space group number
    :return: Lattice type for structure or None if type cannot be detected.

    """
    system = get_crystal_system(sg_number)
    if sg_number in [146, 148, 155, 160, 161, 166, 167]:
        return "rhombohedral"
    elif system == "trigonal":
        return "hexagonal"

    return system


def get_centering_code(sg_number, sg_symbol):
    """get crystal centering codes, to convert from primitive to conventional

    :param sg_number: the space group number
    :param sg_symbol: the space group symbol
    :return: CRYSTAL centering code
    """
    lattice_type = get_lattice_type(sg_number)

    if "P" in sg_symbol or lattice_type == "hexagonal":
        return 1
    elif lattice_type == "rhombohedral":
        # can also be P_R (if a_length == c_length in conventional cell),
        # but crystal doesn't appear to use that anyway
        return 1
    elif "I" in sg_symbol:
        return 6
    elif "F" in sg_symbol:
        return 5
    elif "C" in sg_symbol:
        crystal_system = get_crystal_system(sg_number, as_number=False)
        if crystal_system == "monoclinic":
            return 4  # TODO this is P_C but don't know what code it is, maybe 3?
            # [[1.0, -1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        return 4
    # elif "A" in sg_symbol:
    #     return 2  # TODO check this is always correct (not in original function)

    return 1


def frac2cart(lattice, fcoords):
    """a function that takes the cell parameters, in angstrom, and a list of fractional coordinates
    and returns the structure in cartesian coordinates
    """
    ccoords = []
    for i in fcoords:
        x = i[0] * lattice[0][0] + i[1] * lattice[1][0] + i[2] * lattice[2][0]
        y = i[0] * lattice[0][1] + i[1] * lattice[1][1] + i[2] * lattice[2][1]
        z = i[0] * lattice[0][2] + i[1] * lattice[1][2] + i[2] * lattice[2][2]
        ccoords.append([x, y, z])
    return ccoords


def cart2frac(lattice, ccoords):
    """a function that takes the cell parameters, in angstrom, and a list of Cartesian coordinates
    and returns the structure in fractional coordinates
    """
    det3 = np.linalg.det

    latt_tr = np.transpose(lattice)

    fcoords = []
    det_latt_tr = np.linalg.det(latt_tr)
    for i in ccoords:
        a = (det3([[i[0], latt_tr[0][1], latt_tr[0][2]], [
            i[1], latt_tr[1][1], latt_tr[1][2]
        ], [i[2], latt_tr[2][1], latt_tr[2][2]]])) / det_latt_tr
        b = (det3([[latt_tr[0][0], i[0], latt_tr[0][2]], [
            latt_tr[1][0], i[1], latt_tr[1][2]
        ], [latt_tr[2][0], i[2], latt_tr[2][2]]])) / det_latt_tr
        c = (det3([[latt_tr[0][0], latt_tr[0][1], i[0]], [
            latt_tr[1][0], latt_tr[1][1], i[1]
        ], [latt_tr[2][0], latt_tr[2][1], i[2]]])) / det_latt_tr
        fcoords.append([a, b, c])
    return fcoords


def _operation_frac_to_cart(lattice, rot, trans):
    """convert symmetry operation from fractional to cartesian

    :param lattice: 3x3 matrix (a, b, c)
    :param rot: 3x3 rotation matrix
    :param trans: 3 translation vector
    :return: (rot, trans)
    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rot = np.dot(lattice_tr, np.dot(rot, lattice_tr_inv)).tolist()
    trans = np.dot(trans, lattice).tolist()
    return rot, trans


def ops_frac_to_cart(ops_flat, lattice):
    """convert a list of flattened fractional symmetry operations to cartesian"""
    cart_ops = []
    for op in ops_flat:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = _operation_frac_to_cart(lattice, rot, trans)
        cart_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return cart_ops


def _operation_cart_to_frac(lattice, rot, trans):
    """convert symmetry operation from cartesian to fractional

    :param lattice: 3x3 matrix (a, b, c)
    :param rot: 3x3 rotation matrix
    :param trans: 3 translation vector
    :return: (rot, trans)
    """
    lattice_tr = np.transpose(lattice)
    lattice_tr_inv = np.linalg.inv(lattice_tr)
    rot = np.dot(lattice_tr_inv, np.dot(rot, lattice_tr)).tolist()
    trans = np.dot(trans, np.linalg.inv(lattice)).tolist()

    return rot, trans


def ops_cart_to_frac(ops_flat, lattice):
    """convert a list of flattened cartesian symmetry operations to fractional"""
    frac_ops = []
    for op in ops_flat:
        rot = [op[0:3], op[3:6], op[6:9]]
        trans = op[9:12]
        rot, trans = _operation_cart_to_frac(lattice, rot, trans)
        frac_ops.append(rot[0] + rot[1] + rot[2] + trans)
    return frac_ops


# pylint: disable=too-many-arguments,too-many-locals
def compute_symmetry_3d(structdata,
                        standardize=True,
                        primitive=False,
                        idealize=False,
                        symprec=0.01,
                        angletol=None):
    """ create 3d geometry input for CRYSTAL17

    :param structdata: "lattice", "atomic_numbers", "ccoords", "equivalent"
    :param standardize: whether to standardize the structure
    :param primitive: whether to create a primitive structure
    :param idealize: whether to idealize the structure
    :param symprec: symmetry precision to parse to spglib
    :param angletol: angletol to parse to spglib
    :return: (structdata, symmdata)

    """
    import spglib
    validate_with_json(structdata, "structure")

    angletol = -1 if angletol is None else angletol

    # first create the cell to pass to spglib
    lattice = structdata["lattice"]
    ccoords = structdata["ccoords"]

    # spglib only uses the atomic numbers to demark inequivalent sites
    inequivalent_sites = (np.array(structdata["atomic_numbers"]) * 1000 +
                          np.array(structdata["equivalent"])).tolist()

    if "kinds" in structdata:
        inequivalent_to_kind = {
            i: k
            for i, k in zip(inequivalent_sites, structdata["kinds"])
        }
    else:
        inequivalent_to_kind = None

    fcoords = cart2frac(lattice, ccoords)
    cell = [lattice, fcoords, inequivalent_sites]
    cell = tuple(cell)

    if standardize or primitive:
        scell = spglib.standardize_cell(
            cell,
            no_idealize=not idealize,
            to_primitive=primitive,
            symprec=symprec,
            angle_tolerance=angletol)
        if scell is None:
            raise ValueError("standardization of cell failed: {}".format(cell))
        cell = scell

        lattice = cell[0].tolist()
        fcoords = cell[1]
        ccoords = frac2cart(lattice, fcoords)
        inequivalent_sites = cell[2].tolist()

    # find symmetry
    # TODO can we get only the symmetry operators accepted by CRYSTAL?
    symm_dataset = spglib.get_symmetry_dataset(
        cell, symprec=symprec, angle_tolerance=angletol)
    if symm_dataset is None:
        # TODO option to use P1 symmetry if can't find symmetry
        raise ValueError("could not find symmetry of cell: {}".format(cell))
    sg_num = symm_dataset[
        'number'] if symm_dataset['number'] is not None else 1
    crystal_type = get_crystal_system(sg_num, as_number=True)

    # format the symmetry operations (fractional to cartesian)
    symops = []
    for rot, trans in zip(symm_dataset["rotations"],
                          symm_dataset["translations"]):
        # rot, trans = operation_frac_to_cart(lattice, rot, trans)
        symops.append(rot[0].tolist() + rot[1].tolist() + rot[2].tolist() +
                      trans.tolist())

    # find and set centering code
    # the origin_setting (aka centering code) refers to how to convert conventional to primitive
    if primitive:
        origin_setting = get_centering_code(sg_num,
                                            symm_dataset["international"])
    else:
        origin_setting = 1

    equivalent = np.mod(inequivalent_sites, 1000).tolist()
    atomic_numbers = ((np.array(inequivalent_sites) - np.array(equivalent)) /
                      1000).astype(int).tolist()

    # from jsonextended import edict
    # edict.pprint(symm_dataset)

    structdata = {
        "lattice": lattice,
        "ccoords": ccoords,
        "pbc": [True, True, True],
        "atomic_numbers": atomic_numbers,
        "equivalent": equivalent
    }

    if inequivalent_to_kind:
        structdata["kinds"] = [
            inequivalent_to_kind[i] for i in inequivalent_sites
        ]

    symmdata = {
        "space_group": sg_num,
        "operations": symops,
        "crystal_type": crystal_type,
        "centring_code": origin_setting,
        "equivalent": symm_dataset["equivalent_atoms"].tolist()
    }

    return structdata, symmdata


def get_3d_symmetric_struct(structure,
                            standardize=True,
                            primitive=False,
                            idealize=False,
                            symprec=0.01,
                            angletol=None):
    """ create structure, operations and symmetrically equivalent atoms

    :param structdata: "lattice", "atomic_numbers", "ccoords", "equivalent"
    :param standardize: whether to standardize the structure
    :param primitive: whether to create a primitive structure
    :param idealize: whether to idealize the structure
    :param symprec: symmetry precision to parse to spglib
    :param angletol: angletol to parse to spglib
    :return: (structure, operations, equivalent, crystal_type)

    """
    sdict = structure_to_dict(structure)
    structdata, symmdata = compute_symmetry_3d(sdict, standardize, primitive,
                                               idealize, symprec, angletol)
    new_struct = dict_to_structure(structdata)

    return new_struct, symmdata
