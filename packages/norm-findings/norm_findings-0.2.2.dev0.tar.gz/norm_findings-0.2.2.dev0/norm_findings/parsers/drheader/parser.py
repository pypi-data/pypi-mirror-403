# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import json
from norm_findings.stubs.models import Endpoint, Finding

class DrHeaderParser():

    def get_scan_types(self):
        return ['DrHeader JSON Importer']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import result of DrHeader JSON output.'

    def return_finding(self, test, finding, url=None):
        title = ('Header : ' + finding['rule'])
        message = (((finding['message'] + '\nURL : ') + url) if (url is not None) else finding['message'])
        if (finding.get('value') is not None):
            message += ('\nObserved values: ' + finding['value'])
        if (finding.get('expected') is not None):
            message += '\nExpected values: '
            for expect in finding['expected']:
                if (expect == finding['expected'][(- 1)]):
                    message += expect
                else:
                    message += (expect + '; ')
        severity = finding['severity'].title()
        find = Finding(title=title, test=test, description=message, severity=severity, static_finding=False)
        if (url is not None):
            find.unsaved_endpoints = [Endpoint.from_uri(url)]
        return find

    def get_findings(self, scan_file, test):
        items = []
        try:
            data = json.load(scan_file)
        except ValueError:
            data = {}
        if ((data != {}) and (data[0].get('url') is not None)):
            for item in data:
                url = item['url']
                items.extend((self.return_finding(test=test, finding=finding, url=url) for finding in item['report']))
            return items
        items.extend((self.return_finding(test=test, finding=finding) for finding in data))
        return items
