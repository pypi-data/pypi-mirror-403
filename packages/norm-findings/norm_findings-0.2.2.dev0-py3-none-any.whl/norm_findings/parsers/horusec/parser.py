# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from datetime import datetime
from dateutil.parser import parse
from norm_findings.stubs.models import Finding
from norm_findings.parsers.parser_test import ParserTest

class HorusecParser():
    'Horusec (https://github.com/ZupIT/horusec)'
    ID = 'Horusec'
    CONDIFDENCE = {'LOW': 7, 'MEDIUM': 4, 'HIGH': 1}

    def get_scan_types(self):
        return [f'{self.ID} Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'JSON output of Horusec cli.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        report_date = datetime.strptime(data.get('createdAt')[0:10], '%Y-%m-%d')
        return [self._get_finding(node, report_date) for node in data.get('analysisVulnerabilities')]

    def get_tests(self, scan_type, scan):
        data = json.load(scan)
        report_date = parse(data.get('createdAt'))
        test = ParserTest(name=self.ID, parser_type=self.ID, version=data.get('version').lstrip('v'))
        test.description = '\n'.join([f"**Status:** {data.get('status')}", '**Errors:**', '```', data.get('errors').replace('```', '``````'), '```'])
        test.findings = [self._get_finding(node, report_date) for node in data.get('analysisVulnerabilities')]
        return [test]

    def _get_finding(self, data, date):
        description = '\n'.join([data['vulnerabilities']['details'].split('\n')[(- 1)], '**Code:**', f"```{data['vulnerabilities']['language']}", data['vulnerabilities']['code'].replace('```', '``````').replace('\x00', ''), '```'])
        finding = Finding(title=data['vulnerabilities']['details'].split('\n')[0], date=date, severity=data['vulnerabilities']['severity'].title(), description=description, file_path=data['vulnerabilities']['file'], scanner_confidence=self.CONDIFDENCE[data['vulnerabilities']['confidence']])
        if (data['vulnerabilities'].get('line') and data['vulnerabilities']['line'].isdigit()):
            finding.line = int(data['vulnerabilities']['line'])
        return finding
