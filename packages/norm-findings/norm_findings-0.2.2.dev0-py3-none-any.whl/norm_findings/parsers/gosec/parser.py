# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class GosecParser():

    def get_scan_types(self):
        return ['Gosec Scanner']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Gosec Scanner findings in JSON format.'

    def get_findings(self, scan_file, test):
        tree = scan_file.read()
        try:
            data = json.loads(str(tree, 'utf-8'))
        except Exception:
            data = json.loads(tree)
        dupes = {}
        for item in data['Issues']:
            impact = ''
            references = ''
            findingdetail = ''
            title = ''
            scan_file = item.get('file')
            line = item.get('line')
            scanner_confidence = item.get('confidence')
            title = ((item['details'] + ' - rule ') + item['rule_id'])
            findingdetail += f'''Filename: {scan_file}

'''
            findingdetail += f'''Line number: {line}

'''
            findingdetail += f'''Issue Confidence: {scanner_confidence}

'''
            findingdetail += 'Code:\n\n'
            findingdetail += '```{}```'.format(item['code'])
            sev = item['severity']
            references = 'https://securego.io/docs/rules/{}.html'.format(item['rule_id']).lower()
            if scanner_confidence:
                if (scanner_confidence == 'HIGH'):
                    scanner_confidence = 1
                elif (scanner_confidence == 'MEDIUM'):
                    scanner_confidence = 4
                elif (scanner_confidence == 'LOW'):
                    scanner_confidence = 7
            if ('-' in line):
                line = line.split('-', 1)[0]
            line = (int(line) if line.isdigit() else None)
            dupe_key = ((title + item['file']) + str(line))
            if (dupe_key in dupes):
                find = dupes[dupe_key]
            else:
                dupes[dupe_key] = True
                find = Finding(title=title, test=test, description=findingdetail, severity=sev.title(), impact=impact, references=references, file_path=scan_file, line=line, scanner_confidence=scanner_confidence, static_finding=True)
                dupes[dupe_key] = find
        return list(dupes.values())
