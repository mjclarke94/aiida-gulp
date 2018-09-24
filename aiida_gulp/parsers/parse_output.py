from aiida_gulp import __version__


def parse_output(main_path, parser_class, final=False):
    """

    :type main_path: str
    :type parser_class: str
    :param final: whether to expect 'final' data
    :rtype: (bool, dict)
    """
    psuccess = True
    data = {
        'parser_errors': [],
        'parser_class': str(parser_class),
        'parser_version': __version__,
        "warnings": [],
        "errors": []
    }

    with open(main_path) as f:
        outstr = f.read()
    try:
        _parse_main_output(outstr, data)
    except KeyError as err:
        data['parser_errors'].append("{}".format(err))
        psuccess = False

    if data['errors']:
        psuccess = False

    idata = None
    fdata = None
    if "initial" in data:
        idata = data.pop('initial')
    else:
        data['parser_errors'].append("expected 'initial' data")
        psuccess = False
    if 'final' in data:
        fdata = data.pop('final')
    elif final:
        data['parser_errors'].append("expected 'final' data")
        psuccess = False

    if final:
        if idata:
            data['energy_initial'] = idata['lattice_energy']['primitive']
        if fdata:
            data['energy'] = fdata['lattice_energy']['primitive']
    elif idata:
        data['energy'] = idata['lattice_energy']['primitive']

    return psuccess, data


_reaxff_ename_map = {
    'bond': 'Bond',
    'bpen': 'Double-Bond Valence Angle Penalty',
    'lonepair': 'Lone-Pair',
    'over': 'Coordination (over)',
    'under': 'Coordination (under)',
    'val': 'Valence Angle',
    'pen': 'Double-Bond Valence Angle Penalty',
    'coa': 'Valence Angle Conjugation',
    'tors': 'Torsion',
    'conj': 'Conjugation',
    'hb': 'Hydrogen Bond',
    'vdw': 'van der Waals',
    'coulomb': 'Coulomb',
    'self': 'Charge Equilibration'
}


def _new_line(lines, num_lines=1):
    line = ''
    fields = []
    for _ in range(num_lines):
        line = lines.pop(0).strip()
        fields = line.split()
    return line, fields


def _assert_true(data, condition, msg, line):
    if not condition:
        data["errors"].append("Parsing Error: {} for line: {}".format(
            msg, line))
        return False
    return True


def _parse_main_output(outstr, data):

    data["energy_units"] = "eV"

    lines = outstr.splitlines()

    while lines:
        line, fields = _new_line(lines)

        # if ' '.join(fields[:4]) == 'Total number atoms/shells =':
        #     data['natoms'] = int(fields[4])
        # elif ' '.join(fields[:2]) == 'Formula =':
        #     data['formula'] = fields[2]

        if line.startswith('!! ERROR'):
            data["errors"].append(line)
            return data

        if line.startswith('!! WARNING'):
            data["warnings"].append(line)

        if ' '.join(fields[:4]) == '**** Optimisation achieved ****':
            data['optimised'] = True
        elif "No variables to optimise - single point performed" in line:
            data['optimised'] = True
            data['warnings'].append(
                "No variables to optimise - single point performed")
        elif ' '.join(
                fields[:4]) == '**** Too many failed' and len(fields) > 5:
            if fields[6] == 'optimise':
                data['optimised'] = False
                data['errors'].append(line)
        elif ' '.join(fields[:2]) == '**** Maximum' and len(fields) > 7:
            if ' '.join(fields[4:5] + [fields[8]]) == 'function calls reached':
                data['optimised'] = False
                data['errors'].append(line)

        elif ' '.join(fields[:4]) == 'Total lattice energy =':
            _extract_lattice_energy_prim_only(data, fields)

        elif ' '.join(fields[:4]) == 'Total lattice energy :':
            _extract_lattice_energy(data, lines)

        elif ' '.join(fields[:4]) == 'ReaxFF : Energy contributions:':
            _extract_energy_contribs(data, lines)

        # TODO Total CPU time, num_opt_steps, charges (reaxff only)


def _extract_lattice_energy_prim_only(data, fields):
    """extract energy when there is only a primitive cell"""
    units = ' '.join(fields[5:])
    if units == 'eV':

        energy = float(fields[4])

        etype = 'initial'
        if 'initial' in data:
            if 'lattice_energy' in data['initial']:
                if 'final' not in data:
                    data['final'] = {}
                etype = 'final'
        else:
            data['initial'] = {}
        data[etype]['lattice_energy'] = {}
        data[etype]['lattice_energy']['primitive'] = energy


def _extract_lattice_energy(data, lines):
    """extract energy when there is a primitive and conventional cell"""
    etype = 'initial'
    if 'initial' in data:
        if 'lattice_energy' in data['initial']:
            if 'final' not in etype:
                data['final'] = {}
            etype = 'final'
    else:
        data['initial'] = {}
    data[etype]['lattice_energy'] = {}
    line, fields = _new_line(lines)
    if _assert_true(data, fields[0] == 'Primitive', "expecting primitive energy", line) and \
            _assert_true(data, fields[5] == 'eV', "expecting energy in eV", line):
        data[etype]['lattice_energy']['primitive'] = float(fields[4])
    line, fields = _new_line(lines)
    if _assert_true(data, fields[0] == 'Non-primitive', "expecting non-primitive energy", line) and \
            _assert_true(data, fields[5] == 'eV', "expecting energy in eV", line):
        data[etype]['lattice_energy']['conventional'] = float(fields[4])


def _extract_energy_contribs(data, lines):
    data['energy_contributions'] = {}
    line, fields = _new_line(lines, 2)
    while "=" in line and "E" in line:
        name = _reaxff_ename_map[fields[0][2:-1]]
        if _assert_true(data, fields[3] == 'eV', "expecting energy in eV",
                        line):
            data['energy_contributions'][name] = float(fields[2])
        line, fields = _new_line(lines)
