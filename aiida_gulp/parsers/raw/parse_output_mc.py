#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Matt Clarke
#
# This file is part of aiida-gulp.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
"""
parse the main.gout file of a GULP run and create the required output nodes
"""
import re

from aiida_gulp import __version__
from aiida_gulp.parsers.raw.parse_output_common import (
    read_energy_components,
    read_gulp_table,
)


def parse_file(file_obj, parser_class=None):
    """parse a file resulting from a GULP MC run,
    where one structure (configuration) has been supplied
    """
    content = file_obj.read()
    lines = content.splitlines()

    lines_length = len(lines)

    output = {
        "parser_version": __version__,
        "parser_class": parser_class,
        "parser_errors": [],
        "parser_warnings": [],
        "warnings": [],
        "errors": [],
        "trials": [],
        "energy_units": "eV",
    }

    if not lines:
        return output, "ERROR_STDOUT_EMPTY"

    lineno = 0
    section = "heading"

    while lineno < lines_length:

        line = lines[lineno]
        lineno += 1

        if line.strip().startswith("!! ERROR"):
            output["errors"].append(line.strip())
            continue

        if line.strip().startswith("!! WARNING"):
            output["warnings"].append(line.strip())
            continue

        if section == "heading":

            version = re.findall(
                "\\* Version = ([0-9]+\\.[0-9]+\\.[0-9]+) \\* Last modified", line
            )
            if version:
                output["gulp_version"] = version[0]
                continue

            if line.strip().startswith("*  Output for configuration"):
                section = "output"
                continue

            if lineno >= lines_length:
                output["parser_errors"].append(
                    "Reached end of file before finding output section"
                )
                continue

        if section == "output":

            optimise_start = re.findall("*  Monte Carlo", line)
            if optimise_start:
                section = "monte_carlo"
                continue

        if section == "monte_carlo":
            if line.strip().startswith("Trials"):
                lineno, output["trials"] = read_mc_trials(
                    lines, lineno, star_to_none=True, return_atoms=False
                )
                section = "post_mc"
                output["mc_succeeded"] = True
                continue

        if section == "output":

            if line.strip().startswith("Components of energy :"):
                energy, penergy = ("initial_energy", "initial_primitive_energy")
                try:
                    output[energy], output[penergy], lineno = read_energy_components(
                        lines, lineno
                    )
                except (IOError, ValueError) as err:
                    output["parser_errors"].append(str(err))
                continue

        if section == "post_mc":

            if line.strip().startswith("Monte Carlo properties :"):
                lineno, output["mc_properties"] = read_mc_properties(lines, lineno)

            if line.strip().startswith("Acceptance ratios :"):
                lineno, output["acceptance_ratios"] = read_acceptance_ratio(
                    lines, lineno
                )

            if line.strip().startswith("Final fractional coordinates of atoms"):
                # output for surfaces and polymers
                try:
                    lineno, output["final_coords"] = read_gulp_table(
                        lines,
                        lineno,
                        ["id", "label", "type", "x", "y", "z", "radius"],
                        [int, str, str, float, float, float, float],
                    )
                except (IOError, ValueError) as err:
                    output["parser_errors"].append(str(err))
                continue

            if line.strip().startswith("Peak dynamic memory used"):
                # 'Peak dynamic memory used =       0.56 MB'
                mem_match = re.findall(
                    "Peak dynamic memory used[\\s]*=[\\s]*([+-]?[0-9]*[.]?[0-9]+) MB",
                    line,
                )
                if mem_match:
                    output["peak_dynamic_memory_mb"] = float(mem_match[0])
                continue

            if line.strip().startswith("Total CPU time"):
                # 'Total CPU time  0.0187'
                mem_match = re.findall(
                    "Total CPU time[\\s]*([+-]?[0-9]*[.]?[0-9]+)", line
                )
                if mem_match:
                    output["total_time_second"] = float(mem_match[0])
                continue

    return (
        output,
        assign_exit_code(
            output.get("mc_succeeded", None),
            output["errors"],
            output["parser_errors"],
        ),
    )


def assign_exit_code(
    mc_succeeded, gulp_errors, parser_errors
):  # TODO: Create actual error codes to correspond to the below
    """ given the error messages, assign an exit code """
    if len(gulp_errors) > 0:
        e = gulp_errors[0]  # Base error on first error code if multiple

        mc_input_errors = [
            "Monte Carlo volume is missing from input",
            "chemical potential is missing from input",
            "creation probability is missing from input",
            "destruction probability is missing from input",
            "lowest MC value is missing from input",
            "maximum displacement is missing from input",
            "maximum rotation is missing from input",
            "maximum strain is missing from input",
            "mean MC value is missing from input",
            "molecule information is missing from input",
            "move probability is missing from input",
            "number of steps is missing from input",
            "number of trials is missing from input",
            "numbers of GCMC existing molecules missing from input",
            "output frequency is missing from input",
            "rotation probability is missing from input",
            "strain probability is missing from input",
            "swap probability is missing from input",
        ]
        for input_error in mc_input_errors:
            if input_error in e:
                return "ERROR_MISSING_MC_INPUT"

        if "GCMC species not in full species list" in e:
            return "ERROR_GCMC_SPECIES_NOT_IN_SPECIES_LIST"

        elif (
            "atoms in GCMC existing molecules exceed total number of atoms for cfg" in e
        ):
            return "ERROR_GCMC_MOLECULES_EXCEED_TOTAL"

        elif "error in input for GCMC molecule atoms" in e:
            return "ERROR_GCMC_MOLECULE_INPUT"

        elif "inconsistency in mcmolinsert for ntrialatom" in e:
            return "ERROR_MCMOLINSERT_INCONSISTENCY"

        elif "invalid value for newmol in mcmolconnect" in e:
            return "ERROR_INVALID_NEWMOL_CONNECT"

        elif "invalid value for newmol in mcmolinsert" in e:
            return "ERROR_INVALID_NEWMOL_INSERT"

        elif "line rotation not yet implemented" in e:
            return "ERROR_LINE_ROTATION_NOT_IMPLEMENTED"

        elif "number of species specified for swap only is zero" in e:
            return "ERROR_NO_SWAP_SPECIES"

        elif "periodic molecule chosen for rotation" in e:
            return "ERROR_PERIODIC_MOLECULE_ROTATION"

        elif "strain maximum is too large" in e:
            return "ERROR_STRAIN_MAX_TOO_LARGE"

        elif "strain probability cannot be used in a conv calculation" in e:
            return "ERROR_STAIN_PROB_IN_CONV"

        elif "swap requested but no meaningful swap possible" in e:
            return "ERROR_NO_MEANINGFUL_SWAP_POSSIBLE"

        elif "too many rotation types in input" in e:
            return "ERROR_TOO_MANY_ROTATION_TYPES"
        else:
            return "ERROR_GULP_UNHANDLED"

    elif len(parser_errors) > 1:
        return "ERROR_PARSING_STDOUT"

    # elif opt_succeeded is None and not single_point_only:
    # #     return "ERROR_GULP_UNHANDLED"
    elif mc_succeeded is True:  # Todo...what if it doesn't?
        return None
    return None


def read_mc_trials(lines, lineno, star_to_none=True, return_atoms=False):
    """Read tables of the format:

    ::

    Trials:       100 Accepted:        64 Mean E/N:   -95151.734417 12500.000000
    Trials:       200 Accepted:       117 Mean E/N:   -95275.221729 12500.000000
    Trials:       300 Accepted:       169 Mean E/N:   -95348.652188 12500.000000
    Trials:       400 Accepted:       203 Mean E/N:   -95382.406162 12500.000000
                                        ...


    Parameters
    ----------
    lines: list[str]
    lineno: int
    star_to_none: bool
        See notes below, if a value has been replaced with `***` then convert it to None
    returns_atoms: bool
        If True, returns the number of atoms at each reported MC step. Irrelevant for constant n.

    Returns
    -------
    int: lineno
    values: dict

    Notes
    -----

    Sometimes values can be output as `*`'s (presumably if they are too large)

    ::

        Trials:       400 Accepted:       203 Mean E/N:   ************ 12500.000000



    """
    values = {field: [] for field in ["trials", "accepted", "mean_energy", "natoms"]}

    start_lineno = lineno
    line = lines[lineno]

    while not line.strip().startswith("Trials"):
        lineno += 1

        if lineno >= len(lines):
            raise IOError(
                "reached end of file trying to find start of table, "
                "starting from line #{}".format(start_lineno)
            )

        line = lines[lineno]

    while line.strip().startswith("Trials"):
        lineno += 1
        if lineno >= len(lines):
            raise IOError(
                "reached end of file trying to find end of table, "
                "starting from line #{}".format(start_lineno)
            )

        trials, accepted, mean_energy, natoms = re.findall(
            "([+-]?[0-9]*[.]?[0-9]+)", line
        )

        trials = int(trials)
        accepted = int(accepted)

        if mean_energy.startswith("******") and star_to_none:
            mean_energy = None
        elif not mean_energy.startswith("******"):
            mean_energy = float(mean_energy)

        natoms = float(natoms)

        values["trials"].append(trials)
        values["accepted"].append(accepted)
        values["mean_energy"].append(mean_energy)
        values["natoms"].append(natoms)

        line = lines[lineno]

    if not return_atoms:
        del values["natoms"]

    return lineno, values


def read_acceptance_ratio(lines, lineno):
    """Read tables of the format:

    ::

    --------------------------------------------------------------------------------
     Operation          Attempts            Accepted            %Accepted
    --------------------------------------------------------------------------------
     Translation                   x                   x           x.xxxx
                                        ...
    --------------------------------------------------------------------------------
     Total                         y                   y           y.y
    --------------------------------------------------------------------------------



    Parameters
    ----------
    lines: list[str]
    lineno: int

    Returns
    -------
    int: lineno
    values: dict['str': dict['str': float]]



    """
    values = {}

    start_lineno = lineno
    line = lines[lineno]

    while not line.strip().startswith("Operation"):
        lineno += 1

        if lineno >= len(lines):
            raise IOError(
                "reached end of file trying to find start of table, "
                "starting from line #{}".format(start_lineno)
            )

        line = lines[lineno]

    lineno += 2  # Skip ---- line
    line = lines[lineno]

    while not line.strip().startswith("----"):
        lineno += 1
        if lineno >= len(lines):
            raise IOError(
                "reached end of file trying to find end of table, "
                "starting from line #{}".format(start_lineno)
            )

        operation_type = line.split()[0]
        attempts, accepted, percentage = re.findall("([+-]?[0-9]*[.]?[0-9]+)", line)

        attempts = int(attempts)
        accepted = int(accepted)
        percentage = float(percentage)

        values[operation_type] = {
            "attempts": attempts,
            "accepted": accepted,
            "percentage": percentage,
        }

        line = lines[lineno]

    attempts = 0
    accepted = 0
    for operation, vals in values.items():
        attempts += vals["attempts"]
        accepted += vals["accepted"]
    percentage = accepted / attempts

    values["Total"] = {
        "attempts": attempts,
        "accepted": accepted,
        "percentage": percentage,
    }

    lineno += 3  # Calculate total internally rather than parsing

    return lineno, values


def read_mc_properties(lines, lineno):
    values = {}

    start_lineno = lineno
    line = lines[lineno]

    while not line.strip().startswith("Monte Carlo properties"):
        lineno += 1

        if lineno >= len(lines):
            raise IOError(
                "reached end of file trying to find start of table, "
                "starting from line #{}".format(start_lineno)
            )

        line = lines[lineno]

    lineno += 2
    line = lines[lineno]

    while line.strip() != "":
        lineno += 1

        parameter = line.strip().split()[:-2]
        parameter = "_".join(parameter).lower()

        v = re.findall("([+-]?[0-9]*[.]?[0-9]+)", line)[0]

        values[parameter] = float(v)

        line = lines[lineno]
    return lineno, values
