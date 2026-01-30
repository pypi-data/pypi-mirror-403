# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class MozillaObservatoryParser():
    '\n    Mozilla Observatory\n\n    See: https://observatory.mozilla.org\n\n    See: https://github.com/mozilla/observatory-cli\n\n    See: https://github.com/mozilla/http-observatory\n    '

    def get_scan_types(self):
        return ['Mozilla Observatory Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Mozilla Observatory Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import JSON report.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        nodes = data.get('tests', data)
        findings = []
        for key in nodes:
            node = nodes[key]
            description = '\n'.join([(('**Score Description** : `' + node['score_description']) + '`'), (((('**Result** : `' + node['result']) + '`**expectation** : ') + str(node.get('expectation'))) + '`')])
            finding = Finding(title=node['score_description'], test=test, active=(not node['pass']), description=description, severity=self.get_severity(int(node['score_modifier'])), static_finding=False, dynamic_finding=True, vuln_id_from_tool=node.get('name', key))
            findings.append(finding)
        return findings

    def get_severity(self, num_severity):
        if (0 > num_severity >= (- 10)):
            return 'Low'
        if ((- 11) >= num_severity > (- 26)):
            return 'Medium'
        if (num_severity <= (- 26)):
            return 'High'
        return 'Info'
