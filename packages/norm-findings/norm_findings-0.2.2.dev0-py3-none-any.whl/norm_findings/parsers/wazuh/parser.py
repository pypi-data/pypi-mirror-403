# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import json
from norm_findings.parsers.wazuh.v4_7 import WazuhV4_7
from norm_findings.parsers.wazuh.v4_8 import WazuhV4_8

class WazuhParser():
    '\n    The vulnerabilities with condition "Package unfixed" are skipped because there is no fix out yet.\n    https://github.com/wazuh/wazuh/issues/14560\n    '

    def get_scan_types(self):
        return ['Wazuh']

    def get_label_for_scan_types(self, scan_type):
        return 'Wazuh'

    def get_description_for_scan_types(self, scan_type):
        return 'Wazuh'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        if (not data):
            return []
        if data.get('data'):
            return WazuhV4_7().parse_findings(test, data)
        if data.get('hits'):
            return WazuhV4_8().parse_findings(test, data)
        return []
