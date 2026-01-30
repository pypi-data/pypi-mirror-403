# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import hashlib
import json
import hyperlink
from norm_findings.stubs.models import Endpoint, Finding

class WFuzzParser():
    'A class that can be used to parse the WFuzz JSON report files'

    def severity_mapper(self, severity_input):
        if (200 <= int(severity_input) <= 299):
            return 'High'
        if (300 <= int(severity_input) <= 399):
            return 'Low'
        if (400 <= int(severity_input) <= 499):
            return 'Medium'
        if (int(severity_input) >= 500):
            return 'Low'
        return None

    def get_scan_types(self):
        return ['WFuzz JSON report']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import WFuzz findings in JSON format.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        dupes = {}
        for item in data:
            url = hyperlink.parse(item['url'])
            return_code = item.get('code', None)
            severity = ('Low' if (return_code is None) else self.severity_mapper(severity_input=return_code))
            description = f'''The URL {url.to_text()} must not be exposed
 Please review your configuration
'''
            dupe_key = hashlib.sha256((url.to_text() + str(return_code)).encode('utf-8')).hexdigest()
            if (dupe_key in dupes):
                finding = dupes[dupe_key]
                finding.nb_occurences += 1
            else:
                finding = Finding(title=f'Found {url.to_text()}', test=test, severity=severity, description=description, mitigation='N/A', static_finding=False, dynamic_finding=True, cwe=200, nb_occurences=1)
                finding.unsaved_endpoints = [Endpoint(path='/'.join(url.path), host=url.host, protocol=url.scheme, port=url.port)]
                finding.unsaved_req_resp = [{'req': item['payload'], 'resp': str(return_code)}]
                dupes[dupe_key] = finding
        return list(dupes.values())
