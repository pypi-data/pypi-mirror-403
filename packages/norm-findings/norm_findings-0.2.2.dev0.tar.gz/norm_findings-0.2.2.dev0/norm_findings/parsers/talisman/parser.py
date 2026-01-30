# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding

class TalismanParser():
    'A class that can be used to parse the Talisman JSON report files'

    def get_scan_types(self):
        'Get scan type'
        return ['Talisman Scan']

    def get_label_for_scan_types(self, scan_type):
        'Get label for scan type'
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        'Get description for scan type'
        return 'Import Talisman Scan findings in JSON format.'

    def get_findings(self, scan_file, test):
        'Converts a Talisman JSON report to DefectDojo findings'
        if (scan_file is None):
            return []
        json_data = json.load(scan_file)
        results = json_data.get('results')
        dupes = {}
        for result in results:
            file_path = result['filename']
            for issue in result['failure_list']:
                if issue['commits']:
                    message = issue['message']
                    commit_ids = issue['commits']
                    severity = issue['severity'].capitalize()
                    title = f'Secret pattern found in {file_path} file'
                    description = ''
                    if file_path:
                        description += f'''**File path:** {file_path}
'''
                    if severity:
                        description += f'''**Severity:** {severity}
'''
                    if message:
                        description += f'''**Message:** {message}
'''
                    if commit_ids:
                        description += f'''**Commit hash:** {commit_ids}
'''
                    finding = Finding(title=title, test=test, description=description, cwe=798, file_path=file_path, dynamic_finding=False, static_finding=True, severity=severity)
                    key = hashlib.md5(((((title + message) + file_path) + description) + severity).encode('utf-8'), usedforsecurity=False).hexdigest()
                    if (key not in dupes):
                        dupes[key] = finding
        return list(dupes.values())
