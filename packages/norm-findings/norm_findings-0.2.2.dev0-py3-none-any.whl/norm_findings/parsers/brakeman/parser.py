# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

__author__ = 'feeltheajf'
import json
from dateutil import parser
from norm_findings.stubs.models import Finding

class BrakemanParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Brakeman Parser.\n\n        Fields:\n        - title: Made by joining warning_type and message provided by Brakeman Scanner.\n        - description: Made by joining filename, line number, issue confidence, code, user input, and render path provided by Brakeman Scanner.\n        - severity: Set to Medium regardless of context.\n        - file_path: Set to file from Brakeman Scanner.\n        - line: Set to line from Brakeman Scanner.\n        - date: Set to end_date from Brakeman Scanner.\n        - static_finding: Set to true.\n        '
        return ['title', 'description', 'severity', 'file_path', 'line', 'date', 'static_finding']

    def get_dedupe_fields(self) -> list[str]:
        "\n        Return the list of fields used for deduplication in the Brakeman Parser.\n\n        Fields:\n        - title: Made by joining warning_type and message provided by Brakeman Scanner.\n        - line: Set to line from Brakeman Scanner.\n        - file_path: Set to file from Brakeman Scanner.\n        - description: Made by joining filename, line number, issue confidence, code, user input, and render path provided by Brakeman Scanner.\n\n        NOTE: uses legacy dedupe: ['title', 'cwe', 'line', 'file_path', 'description']\n        NOTE: cwe is not provided by parser.\n        "
        return ['title', 'line', 'file_path', 'description']

    def get_scan_types(self):
        return ['Brakeman Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Brakeman Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import Brakeman Scanner findings in JSON format.'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return ()
        tree = scan_file.read()
        try:
            data = json.loads(str(tree, 'utf-8'))
        except BaseException:
            data = json.loads(tree)
        dupes = {}
        find_date = parser.parse(data['scan_info']['end_time'])
        for item in data['warnings']:
            impact = ''
            findingdetail = ''
            title = ((item['warning_type'] + '. ') + item['message'])
            findingdetail += (('Filename: ' + item['file']) + '\n')
            if (item['line'] is not None):
                findingdetail += (('Line number: ' + str(item['line'])) + '\n')
            findingdetail += (('Issue Confidence: ' + item['confidence']) + '\n\n')
            if (item['code'] is not None):
                findingdetail += (('Code:\n' + item['code']) + '\n')
            if (item['user_input'] is not None):
                findingdetail += (('User input:\n' + item['user_input']) + '\n')
            if (item['render_path'] is not None):
                findingdetail += 'Render path details:\n'
                findingdetail += json.dumps(item['render_path'], indent=4)
            sev = 'Medium'
            references = item['link']
            dupe_key = item['fingerprint']
            if (dupe_key in dupes):
                find = dupes[dupe_key]
            else:
                dupes[dupe_key] = True
                find = Finding(title=title, test=test, description=findingdetail, severity=sev, impact=impact, references=references, file_path=item['file'], line=item['line'], date=find_date, static_finding=True)
                dupes[dupe_key] = find
        return list(dupes.values())
