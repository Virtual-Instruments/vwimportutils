#!/usr/bin/env python
"""
__author__ = 'nick.york, david.dougherty'
__license__ = 'https://www.apache.org/licenses/LICENSE-2.0'
__copyright__ = 'Copyright (c) 2019 Virtual Instruments Corporation. All rights reserved.'
__date__ = '2019-06-30'
__version__ = '1.0'
"""

import click
import json
import os


class Entity:
    def __init__(self, name, etype, child_entities):
        self.name = name
        self.type = etype
        self.child_entities = {"add": child_entities}

    def __lt__(self, other):
        return self.name < other.name

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=2)


class ApplicationEntity:
    def __init__(self, name, etype, initiator_list):
        self.name = name
        self.type = etype
        self.itl_patterns = []
        self.devices = {'add' : []}

        for i in initiator_list:
            if i.count(":") == 2:
                # I:T:L
                self.itl_patterns.append({"edit_type": "add", "initiator": i.split(":")[0], "target": i.split(":")[1], "lun": i.split(":")[2]})
            elif i.count(":") == 1:
                # I:T
                self.itl_patterns.append({"edit_type": "add", "initiator": i.split(":")[0], "target": i.split(":")[1] })
            else:
                self.devices['add'].append(i)
        if len(self.itl_patterns) < 1:
            del(self.itl_patterns)
        if len(self.devices['add']) < 1:
            del(self.devices)

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


@click.command('vw_csv_relations_to_json', short_help='Convert CSV entities to importable JSON')
@click.argument('csv_in', type=click.File('r'))
@click.argument('json_out', type=click.File('w'))
def main(csv_in, json_out):
    """
    This script generates an importable JSON file from a CSV file containing
    entity definitions.

    Input is a CSV file formatted as follows:

    \b
    hba,hba1,hba1port1,hba1port2
    hba,hba2,hba2port1,hba2port2
    host,host1,hba1
    host,host2,hba2
    application,app1,host1,host2

    Output is a JSON file that can be imported into VirtualWisdom, either via
    the UI or via the command line using the vw_import_entities script.

    The command is pipeable; simply replace either the input file, output file,
    or both with a dash (-).

    Examples (Linux/macOS/Unix):

    (venv) $ vw_csv_relations_to_json relations.csv import.json

    (venv) $ cat relations.csv | vw_csv_relations_to_json - - | vw_import_entities ...
    """
    if os.name == 'nt':
        success = 'success'
        fail = 'fail '
    else:
        success = b'\xe2\x9c\x94'.decode('utf-8')
        fail = b'\xe2\x9c\x98'.decode('utf-8') + ' '


    top = Top()

    for line in csv_in:
        if line.count(',') < 2:
            continue
        etype = line.split(',')[0].strip().replace("'", '').replace('"', '')
        name = line.split(',')[1].strip().replace("'", '').replace('"', '')
        members = []
        for member in line.replace("'", '').replace('"', '').split(',')[2:]:
            members.append(member.strip())
        if etype.lower() == 'application':
            top.entities.append(ApplicationEntity(name, etype, members))
        else:
            top.entities.append(Entity(name, etype, members))

    json_out.write(top.to_JSON())
    json_out.write('\n')


if __name__ == '__main__':
    main()
