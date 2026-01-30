# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class GitlabAPIFuzzingParser():
    '\n    GitLab API Fuzzing Report\n\n    Ref: https://gitlab.com/gitlab-org/security-products/security-report-schemas/-/blob/master/dist/coverage-fuzzing-report-format.json\n    '

    def get_scan_types(self):
        return ['GitLab API Fuzzing Report Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'GitLab API Fuzzing Report Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'GitLab API Fuzzing Report report file can be imported in JSON format (option --json).'

    def get_findings(self, scan_file, test):
        findings = []
        data = json.load(scan_file)
        vulnerabilities = data['vulnerabilities']
        for vulnerability in vulnerabilities:
            title = vulnerability['name']
            severity = self.normalise_severity(vulnerability['severity'])
            description = vulnerability.get('category', '')
            if (location := vulnerability.get('location')):
                if (crash_type := location.get('crash_type')):
                    description += f'''
{crash_type}'''
                if (crash_state := location.get('crash_state')):
                    description += f'''
{crash_state}'''
            findings.append(Finding(title=title, test=test, description=description, severity=severity, static_finding=False, dynamic_finding=True, unique_id_from_tool=vulnerability['id']))
        return findings

    def normalise_severity(self, severity):
        "\n        Normalise GitLab's severity to DefectDojo's\n        (Critical, High, Medium, Low, Unknown, Info) -> (Critical, High, Medium, Low, Info)\n        "
        if (severity == 'Unknown'):
            return 'Info'
        return severity
