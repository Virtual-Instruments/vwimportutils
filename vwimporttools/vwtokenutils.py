"""
__author__ = 'david.dougherty'
__license__ = 'https://www.apache.org/licenses/LICENSE-2.0'
__copyright__ = 'Copyright (c) 2018 Virtual Instruments Corporation. All rights reserved.'
__date__ = '2018-12-11'
__version__ = '1.0'
"""


import json
import requests
import time


class VWtokenutils:
    AUTHORIZATION_HEADER = { 'authorization' : 'bearer ' }
    CONTENT_TYPE_HEADER = { 'content-type' : 'application/json' }

    def __init__(self, h, t):
        requests.packages.urllib3.disable_warnings()
        self.session = requests.Session()
        self.host = h
        self.token = t
        self.AUTHORIZATION_HEADER.update({ 'authorization' : 'bearer ' + self.token })

    def get(self, endpoint, parameters=None):
        try:
            r = self.session.get('https://{0}{1}'.format(self.host, endpoint), headers=self.AUTHORIZATION_HEADER, params=parameters, verify=False)
        except requests.exceptions.RequestException as errr:
            return False, "An exception was caught connecting to VW. {}".format(errr)

        try:
            val = r.json()
        except ValueError:
            val = r.text

        if r.status_code == 200:
            return True, val
        else:
            if isinstance(val, dict) and 'errors' in val and len(val['errors']) >= 1:
                return False, "GET to {} failed with status code {} ({})".format(endpoint, r.status_code,
                    val['errors'][0]['code'] + ' ; ' + val['errors'][0]['message'])
            else:
                return False, "GET to {} failed with status_code {} ({})".format(endpoint, r.status_code, val)

    def put(self, endpoint, payload=None, parameters=None):
        headers = self.CONTENT_TYPE_HEADER.copy()
        headers.update(self.AUTHORIZATION_HEADER)
        try:
            r = self.session.put('https://{0}{1}'.format(self.host, endpoint), data=payload, params=parameters, verify=False, headers=headers)
        except requests.exceptions.RequestException as errr:
            return False, "An exception was caught connecting to VW. {}".format(errr)

        try:
            val = r.json()
        except ValueError:
            val = r.text

        if r.status_code == 200:
            return True, val
        else:
            if isinstance(val, dict) and 'errors' in val and len(val['errors']) >= 1:
                return False, "PUT to {} failed with status code {} ({})".format(endpoint, r.status_code,
                    val['errors'][0]['code'] + ' ; ' + val['errors'][0]['message'])
            else:
                return False, "PUT to {} failed with status_code {} ({})".format(endpoint, r.status_code, val)

    def post(self, endpoint, payload, timeout=None):
        headers = self.CONTENT_TYPE_HEADER.copy()
        headers.update(self.AUTHORIZATION_HEADER)
        try:
            r = self.session.post('https://{0}{1}'.format(self.host, endpoint), data=payload, verify=False, timeout=timeout, headers=headers)
        except requests.exceptions.RequestException as errr:
            return False, "An exception was caught connecting to VW. {}".format(errr)

        try:
            val = r.json()
        except ValueError:
            val = r.text

        if r.status_code == 200:
            return True, val
        else:
            if isinstance(val, dict) and 'errors' in val and len(val['errors']) >= 1:
                return False, "POST to {} failed with status code {} ({})".format(endpoint, r.status_code,
                    val['errors'][0]['code'] + ' ; ' + val['errors'][0]['message'])
            else:
                return False, "POST to {} failed with status_code {} ({})".format(endpoint, r.status_code, val)

    def delete(self, endpoint, payload=None, parameters=None):
        headers = self.CONTENT_TYPE_HEADER.copy()
        headers.update(self.AUTHORIZATION_HEADER)
        try:
            r = self.session.delete('https://{0}{1}'.format(self.host, endpoint), data=payload, params=parameters, verify=False, headers=headers)
        except requests.exceptions.RequestException as errr:
            return False, "An exception was caught connecting to VW. {}".format(errr)

        try:
            val = r.json()
        except ValueError:
            val = r.text

        if r.status_code == 200:
            return True, val
        else:
            if isinstance(val, dict) and 'errors' in val and len(val['errors']) >= 1:
                return False, "DELETE to {} failed with status code {} ({})".format(endpoint, r.status_code,
                    val['errors'][0]['code'] + ' ; ' + val['errors'][0]['message'])
            else:
                return False, "DELETE to {} failed with status_code {} ({})".format(endpoint, r.status_code, val)

    @staticmethod
    def process_topxtable_data(entity_metrics, results_data, metric, entity_type):
        for i in range(len(results_data)):
            if metric not in entity_metrics:
                entity_metrics[metric] = {}
            entity_metrics[metric][results_data[i]['entityName']] = {k: results_data[i][k] for k in ('avg','min','max','median','5th','25th','75th','95th')}

        return entity_metrics

    @staticmethod
    def process_topxcard_data(entity_metrics, results_data, metric, entity_type):
        entity_metrics[metric] = { x['entityName'] : x['entityValue'] for x in results_data }
        
        return entity_metrics

    @staticmethod
    def process_topxtrend_data(entity_metrics, results_data, metric, entity_type):
        for i in range(len(results_data)):
            for j in range(len(results_data[i]['data'])):
                entity = results_data[i]['entityName']
                timestamp = results_data[i]['data'][j][0]
                data = results_data[i]['data'][j][1]

                if entity_type not in entity_metrics:
                    entity_metrics[entity_type] = {}
                if entity not in entity_metrics[entity_type]:
                    entity_metrics[entity_type][entity] = {}
                if timestamp not in entity_metrics[entity_type][entity]:
                    entity_metrics[entity_type][entity][timestamp] = {}
                entity_metrics[entity_type][entity][timestamp][metric] = data

        return entity_metrics

    @staticmethod
    def process_histogram_data(entity_metrics, results_data, metric, entity_type):

        if results_data:
            entity_metrics[metric] = results_data

        return entity_metrics

    def get_data(self, payload):
        rc, uuid = self.put('/api/v1/reports/reportBatch', json.dumps(payload))
        if not rc:
            return False, 'reportBatch request failed ({})'.format(uuid)
        data_recvd = False
        parameters = { 'uuid' : uuid }
        while not data_recvd:
            rc, res = self.get('/api/v1/reports/reportPoll', parameters)
            if rc and 'finished' in res and res['finished']:
                data_recvd = True
            else:
                time.sleep(1)
        if 'charts' in res and len(res['charts']) > 0:
            result_data = res['charts'][0]['chartData']
        else:
            result_data = []
        entity_metrics = {}
        entity_metrics = getattr(self, 'process_' + payload['chartType'] + '_data')(entity_metrics, result_data, payload['metricName'], payload['entityType'])

        if len(entity_metrics) > 0:
            return True, entity_metrics
        else:
            return False, 'No data returned for request'

    def get_entities(self, kind, filterType='EXACT_MATCH', filterText=None):
        parameters = {'type' : kind}
        if filterText:
            parameters['filterText'] = filterText
            parameters['filterType'] = filterType
        status_code, status_str = self.get('/api/v1/entities', parameters)
        if not status_code:
            return False, 'Could not get entities of type {} ({})'.format(kind, status_str)
        else:
            return True, [{x['id'] : x['value'] for x in e['properties']} for e in status_str]
