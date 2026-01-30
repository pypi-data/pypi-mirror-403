# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
import re
from dateutil import parser
from norm_findings.stubs.models import Finding

class DawnScannerParser():
    CVE_REGEX = re.compile('CVE-\\d{4}-\\d{4,7}')

    def get_scan_types(self):
        return ['DawnScanner Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Dawnscanner (-j) output file can be imported in JSON format.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        find_date = parser.parse(data['scan_started'])
        items = []
        for item in data['vulnerabilities']:
            findingdetail = (item['message'] if (item['message'][0:2] != 'b,') else item['message'][0:(- 1)])
            finding = Finding(title=item['name'], test=test, description=findingdetail, severity=item['severity'].capitalize(), mitigation=item.get('remediation'), references=item.get('cve_link'), date=find_date, static_finding=True, dynamic_finding=False)
            if item.get('remediation'):
                finding.fix_available = True
            else:
                finding.fix_available = False
            if self.CVE_REGEX.match(item['name']):
                finding.unsaved_vulnerability_ids = [self.CVE_REGEX.findall(item['name'])[0]]
            items.append(finding)
        return items
