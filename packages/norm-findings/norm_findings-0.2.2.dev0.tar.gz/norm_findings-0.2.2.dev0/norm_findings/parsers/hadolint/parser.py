# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class HadolintParser():

    def get_scan_types(self):
        return ['Hadolint Dockerfile check']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Hadolint Dockerfile check findings in JSON format.'

    def get_findings(self, scan_file, test):
        tree = json.load(scan_file)
        return self.get_items(tree, test)

    def get_items(self, tree, test):
        items = {}
        for node in tree:
            item = get_item(node, test)
            unique_key = ((((str(node['line']) + '-') + str(node['column'])) + node['code']) + node['file'])
            items[unique_key] = item
        return items.values()

def get_item(vulnerability, test):
    if ('level' in vulnerability):
        if (vulnerability['level'] == 'error'):
            severity = 'Critical'
        elif (vulnerability['level'] == 'warning'):
            severity = 'High'
        else:
            severity = 'Info'
    else:
        severity = 'Info'
    finding = Finding(title=((vulnerability['code'] + ': ') + vulnerability['message']), test=test, severity=severity, file_path=vulnerability['file'], line=vulnerability['line'], description='Vulnerability ID: {}\nDetails: {}\n'.format(vulnerability['code'], vulnerability['message']), static_finding=True, dynamic_finding=False)
    finding.description = finding.description.strip()
    return finding
