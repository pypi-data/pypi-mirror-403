# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import hashlib
import json
from datetime import datetime
from norm_findings.stubs.models import Endpoint, Finding

class GitlabDastParser():
    'Import GitLab DAST Report in JSON format'

    def get_scan_types(self):
        return ['GitLab DAST Report']

    def get_label_for_scan_types(self, scan_type):
        return 'GitLab DAST Report'

    def get_description_for_scan_types(self, scan_type):
        return 'GitLab DAST Report in JSON format (option --json).'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return None
        return self.get_items(json.load(scan_file), test)

    def get_items(self, tree, test):
        items = {}
        scanner = tree.get('scan', {}).get('scanner', {})
        for node in tree['vulnerabilities']:
            item = self.get_item(node, test, scanner)
            item_key = hashlib.sha256(f'{item.severity}|{item.title}|{item.description}'.encode()).hexdigest()
            if (item_key in items):
                items[item_key].unsaved_endpoints.extend(item.unsaved_endpoints)
                items[item_key].nb_occurences += 1
            else:
                items[item_key] = item
        return list(items.values())

    def get_confidence_numeric(self, confidence):
        switcher = {'Confirmed': 1, 'High': 3, 'Medium': 4, 'Low': 6, 'Experimental': 7, 'Unknown': 8, 'Ignore': 10}
        return switcher.get(confidence)

    def get_item(self, vuln, test, scanner):
        scanner_confidence = self.get_confidence_numeric(vuln.get('confidence', 'Could not be determined'))
        description = f'''Scanner: {scanner.get('name', 'Could not be determined')}
'''
        if ('message' in vuln):
            description += f'''{vuln['message']}
'''
        elif ('description' in vuln):
            description += f'''{vuln['description']}
'''
        finding = Finding(test=test, nb_occurences=1, scanner_confidence=scanner_confidence, description=description, static_finding=False, dynamic_finding=True)
        (request, response) = self.prepare_request_response(vuln.get('evidence'))
        if (request is not None):
            finding.unsaved_req_resp = []
            finding.unsaved_req_resp.append({'req': str(request), 'resp': str(response)})
        if ('discovered_at' in vuln):
            finding.date = datetime.strptime(vuln['discovered_at'], '%Y-%m-%dT%H:%M:%S.%f')
        if ('id' in vuln):
            finding.unique_id_from_tool = vuln['id']
        finding.title = vuln.get('name', finding.unique_id_from_tool)
        for identifier in vuln['identifiers']:
            if (identifier['type'].lower() == 'cwe'):
                finding.cwe = int(identifier['value'])
                break
        if vuln['links']:
            ref = ''.join((f'''{link['url']}
''' for link in vuln['links']))
            ref = ref[:(- 1)]
            finding.references = ref
        if ('severity' in vuln):
            finding.severity = vuln['severity']
        location = vuln.get('location', {})
        if (('hostname' in location) and ('path' in location)):
            url_str = f"{location['hostname']}{location['path']}"
            finding.unsaved_endpoints = [Endpoint.from_uri(url_str)]
        if ('solution' in vuln):
            finding.mitigation = vuln['solution']
        return finding

    def prepare_request_response(self, evidence):
        if (evidence == []):
            return (None, None)
        request = evidence.get('request')
        request_headers = request.get('headers', [])
        reqHeaders = ''
        for header in request_headers:
            reqHeaders += (((('                name: ' + header['name']) + ' | value: ') + header['value']) + '\n')
        returnrequest = ((((('Request Headers:\n' + str(reqHeaders)) + '\nRequest Method: ') + str(request.get('method'))) + '\nRequest URL: ') + str(request.get('url')))
        response = evidence.get('response')
        response_headers = response.get('headers', [])
        respHeaders = ''
        for header in response_headers:
            respHeaders += (((('                name: ' + header['name']) + ' | value: ') + header['value']) + '\n')
        returnresponse = ((((('Response Headers:\n' + str(respHeaders)) + '\nResponse Phrase: ') + str(response.get('reason_phrase'))) + '\nResponse Status Code: ') + str(response.get('status_code')))
        return (returnrequest, returnresponse)
