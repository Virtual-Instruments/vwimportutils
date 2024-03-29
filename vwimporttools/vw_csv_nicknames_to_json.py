#!/usr/bin/env python
"""
__author__ = 'nick.york, david.dougherty'
__license__ = 'https://www.apache.org/licenses/LICENSE-2.0'
__copyright__ = 'Copyright (c) 2021 Virtual Instruments Corporation (d/b/a Virtana). All rights reserved.'
__date__ = '2021-11-15'
__version__ = '1.1'
"""

import click
import json
import os


class Entity:
    def __init__(self, name, wwn, etype):
        self.new_name = name
        self.wwn = wwn
        self.type = etype

    def __lt__(self, other):
        return self.name < other.name

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=2)


class Top:
    def __init__(self):
        self.version = 2
        self.entities = []

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=2)


@click.command('vw_csv_nicknames_to_json', short_help='Convert CSV nicknames to importable JSON')
@click.option('--etype', '-t', prompt='Entity type (either hostport or storageport)')
@click.argument('csv_in', type=click.File('r'))
@click.argument('json_out', type=click.File('w'))
def main(etype, csv_in, json_out):
    """
    This script generates an importable JSON file from a CSV file containing
    WWN to nickname (alias) mappings.

    Input is a CSV file formatted as follows:

    \b
    WWN1,nickname1
    WWN2,nickname2

    Output is a JSON file that can be imported into VirtualWisdom, either via
    the UI or via the command line using the vw_import_entities script.

    The --etype (-t) argument must be either hostport or storageport.

    The command is pipeable; simply replace either the input file, output file,
    or both with a dash (-).

    Examples (Linux/macOS/Unix):

    (venv) $ vw_csv_nicknames_to_json -t hostport aliases.csv import.json

    (venv) $ cat aliases.csv | vw_csv_nicknames_to_json -t hostport - - | vw_import_entities ...
    """
    if os.name == 'nt':
        success = 'success'
        fail = 'fail '
    else:
        success = b'\xe2\x9c\x94'.decode('utf-8')
        fail = b'\xe2\x9c\x98'.decode('utf-8') + ' '


    top = Top()

    for line in csv_in:
        if not ',' in line:
            continue
        top.entities.append(Entity(line.split(',')[1].strip().replace("'", '').replace('"', ''),
            line.split(',')[0].strip(), etype))

    json_out.write(top.to_JSON())
    json_out.write('\n')


if __name__ == '__main__':
    main()
