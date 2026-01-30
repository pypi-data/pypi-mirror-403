# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class KrakenDAuditParser():

    def get_scan_types(self):
        return ['KrakenD Audit Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import JSON reports of KrakenD Audit Scans.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        findings = []
        for recommendation in data.get('recommendations', []):
            rule = recommendation.get('rule', None)
            severity = recommendation.get('severity')
            message = recommendation.get('message', None)
            if (rule is not None):
                finding = Finding(title=(('KrakenD' + '_') + rule), test=test, description=('**Rule:** ' + rule), severity=severity.lower().capitalize(), mitigation=message, static_finding=True, dynamic_finding=False, fix_available=True)
                findings.append(finding)
        return findings
