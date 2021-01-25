#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
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
from aiida_gulp.potentials.base import PotentialWriterAbstract, PotentialContent
from aiida_gulp.potentials.common import INDEX_SEP
from aiida_gulp.validation import load_schema


class PotentialWriterBuckingham(PotentialWriterAbstract):
    """class for creating gulp Buckingham type
    inter-atomic potential inputs
    """

    @classmethod
    def get_description(cls):
        return "Buckingham potential, of the form; E = A*e**(-Br) - C/r**2"

    @classmethod
    def _get_schema(cls):
        return load_schema("potential.buckingham.schema.json")

    @classmethod
    def _get_fitting_schema(cls):
        return load_schema("fitting.buckingham.schema.json")

    def _make_string(self, data, fitting_data=None):
        """write reaxff data in GULP input format

        Parameters
        ----------
        data : dict
            dictionary of data
        species_filter : list[str] or None
            list of atomic symbols to filter by

        Returns
        -------
        str:
            the potential file content
        int:
            number of potential flags for fitting

        """
        lines = []
        total_flags = 0
        num_fit = 0

        for indices in sorted(data["2body"]):
            species = [
                "{:7s}".format(data["species"][int(i)])
                for i in indices.split(INDEX_SEP)
            ]
            values = data["2body"][indices]
            lines.append(
                "buckingham"
            )
            if "buck_rmin" in values:
                values_string = "{buck_A:.8E} {buck_rho:.8E} {buck_C:.8E} {buck_rmin:8.5f} {buck_rmax:8.5f}".format(
                    **values
                )
            else:
                values_string = "{buck_A:.8E} {buck_rho:.8E} {buck_C:.8E} {buck_rmax:8.5f}".format(
                    **values
                )

            total_flags += 2

            if fitting_data is not None:
                flag_a = flag_b = 0
                if "buck_A" in fitting_data.get("2body", {}).get(indices, []):
                    flag_a = 1
                if "buck_rho" in fitting_data.get("2body", {}).get(indices, []):
                    flag_b = 1
                if "buck_C" in fitting_data.get("2body", {}).get(indices, []):
                    flag_c = 1
                num_fit += flag_a + flag_b + flag_c
                values_string += " {} {} {}".format(flag_a, flag_b, flag_c)

            lines.append(" ".join(species) + " " + values_string)

        return PotentialContent("\n".join(lines), total_flags, num_fit)

    def read_exising(self, lines):
        """read an existing potential file

        Parameters
        ----------
        lines : list[str]

        Returns
        -------
        dict
            the potential data

        Raises
        ------
        IOError
            on parsing failure

        """
        lineno = 0
        symbol_set = set()
        terms = {}

        while lineno < len(lines):
            line = lines[lineno]
            if line.strip().startswith("buckingham"):
                meta_values = line.strip().split()
                if len(meta_values) != 1:
                    raise NotImplementedError("Meta-variables not implemented for pair_style buckingham")

                lineno, sset, results = self.read_atom_section(
                    lines,
                    lineno + 1,
                    number_atoms=2,
                )
                symbol_set.update(sset)
                terms.update(results)
            lineno += 1

        pot_data = {"species": sorted(symbol_set), "2body": {}}
        for key, value in terms.items():
            indices = "-".join([str(pot_data["species"].index(term)) for term in key])
            variables = value["values"].split()
            if len(variables) in [4, 6]:
                pot_data["2body"][indices] = {
                    "buck_A": float(variables[0]),
                    "buck_rho": float(variables[1]),
                    "buck_C": float(variables[2]),
                    "buck_rmax": float(variables[3]),
                }
            elif len(variables) in [5, 7]:
                pot_data["2body"][indices] = {
                    "buck_A": float(variables[0]),
                    "buck_rho": float(variables[1]),
                    "buck_C": float(variables[2]),
                    "buck_rmin": float(variables[3]),
                    "buck_rmax": float(variables[4]),
                }
            else:
                raise IOError("expected 4, 5, 6, or 7 variables: {}".format(value))

        return pot_data
