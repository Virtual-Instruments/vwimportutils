#!/usr/bin/env python
"""
__author__ = 'nick.york, david.dougherty'
__license__ = 'https://www.apache.org/licenses/LICENSE-2.0'
__copyright__ = 'Copyright (c) 2019 Virtual Instruments Corporation. All rights reserved.'
__date__ = '2019-12-18'
__version__ = '1.0.1'
"""

import click
import json
import os
import time
from vwimporttools.vwtokenutils import VWtokenutils


def validate_input(json_in):
    try:
        object_in = json.load(json_in)
    except ValueError as e:
        return False, 'Provided JSON could not be parsed: {}'.format(str(e))

    if 'version' not in object_in or object_in['version'] not in (2, '2'):
        return False, 'Provided JSON does not conform to VW entity import standard; version number mismatch'

    if 'entities' not in object_in or len(object_in['entities']) == 0:
        return False, 'Provided JSON contains no entities'

    return True, object_in


def parse_errors(errors_in):
    messages = []
    if 'error' in errors_in and 'message' in errors_in['error']:
        messages.append(errors_in['error']['message'])
    if 'result' in errors_in and 'entities' in errors_in['result']:
        for entity in errors_in['result']['entities']:
            try:
                messages.append('  Message: {}'.format(entity['marker']['message']))
                messages.append('  Location: line {} column {}'.format(
                    entity['marker']['location']['line'],
                    entity['marker']['location']['column']
                ))
                messages.append('  Entity: name = {}, type = {}'.format(
                    entity['name'] if 'name' in entity else '',
                    entity['type'] if 'type' in entity else ''
                ))
            except:
                pass

    return messages


@click.command('vw_csv_relations_to_json', short_help='Convert CSV entities to importable JSON')
@click.option('--host', '-h', prompt='VW hostname or IP', envvar='VI_IPADDR')
@click.option('--token', '-t', prompt='VW API token', envvar='VI_TOKEN')
@click.option('--force', '-F', is_flag=True)
@click.argument('json_in', type=click.File('r'))
def main(host, token, force, json_in):
    """
    This script imports entities (or aliases) into VirtualWisdom. It does
    so using VW's Public REST API. As such, it requires two things: (1) a
    token generated from the VW UI (see Ch. 8 in the VW User Guide), and
    (2) a REST API SDK license, properly installed in the target VW Appliance.

    Input is a properly constructed JSON import file (see Ch. 8 in the VW
    User Guide).

    The command is pipeable; simply replace the input file with a dash (-).

    Examples (Linux/macOS/Unix):

    (venv) $ vw_import_entities -h 10.20.30.40 -t <token> entities.json

    (venv) $ cat aliases.csv | vw_csv_nicknames_to_json - - | vw_import_entities -h 10.20.30.40 -t <token> -

    If your input file has any errors, they will be listed to the screen.

    You can set two environment variables to simplify the use of this script:

    On Mac/Linux/Unix:

    \b
    export VI_IPADDR=10.20.30.40
    export VI_TOKEN=<token>

    On Windows:

    \b
    set VI_IPADDR=10.20.30.40
    set VI_TOKEN=<token>

    Doing so eliminates the need to use the -h and -t options.
    """
    if os.name == 'nt':
        success = 'success'
        fail = 'fail '
    else:
        success = b'\xe2\x9c\x94'.decode('utf-8')
        fail = b'\xe2\x9c\x98'.decode('utf-8') + ' '

    vw = VWtokenutils(host, token)

    click.echo('Validating input... ', nl=False)
    rc, res = validate_input(json_in)
    if rc:
        click.echo(click.style(success, fg='green'))
    else:
        click.echo(click.style(fail, fg='red'), nl=False)
        click.echo(click.style(res, fg='cyan'))
        exit()

    click.echo('Uploading and verifying JSON... ', nl=False)
    rc, res = vw.post('/api/v1/entitiesimport/start', json.dumps(res, sort_keys=True, indent=2))
    if rc and 'status' in res and res['status'] == 'OK':
        transactionId = res['result']['transactionId']
        click.echo(click.style(success, fg='green'))
    else:
        transactionId = res['result']['transactionId']
        click.echo(click.style(fail, fg='red'), nl=False)
        errors = parse_errors(res)
        click.echo(click.style(errors[0], fg='cyan'))
        for e in errors[1:]:
            click.echo(click.style(e, fg='yellow'))
        if not force:
            if transactionId != None:
                _,_ = vw.delete('/api/v1/entitiesimport/discard',
                    '{"async": true, "transactionId": ' + str(transactionId) + '}'
                )
            exit()

    click.echo('Committing JSON... ', nl=False)
    payload = { 'async' : True, 'transactionId' : transactionId }
    rc, res = vw.put('/api/v1/entitiesimport/commit', json.dumps(payload))
    if rc and 'status' in res and res['status'] == 'OK':
        click.echo(click.style(success, fg='green'))
    else:
        click.echo(click.style(fail, fg='red'), nl=False)
        click.echo(click.style('File commit failed: {}'.format(res['errors']['message']), fg='cyan'))
        exit()

    click.echo('Performing final verification... ', nl=False)
    parameters = { 'transactionId' : transactionId }
    while True:
        rc, res = vw.get('/api/v1/entitiesimport/status', parameters=parameters)
        if rc and 'success' in res and res['success'] == False and 'status' in res and res['status'] == 'Busy':
            time.sleep(1)
            continue
        else:
            break
    if rc and 'success' in res and res['success'] == True:
        click.echo(click.style(success, fg='green'))
    else:
        click.echo(click.style(fail, fg='red'), nl=False)
        click.echo(click.style('File import failed: {}'.format(res['errors']['message']), fg='cyan'))
        exit()


if __name__ == '__main__':
    main()
