# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class GitlabDepScanParser():

    def get_scan_types(self):
        return ['GitLab Dependency Scanning Report']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import GitLab SAST Report vulnerabilities in JSON format.'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return None
        tree = self.parse_json(scan_file)
        if tree:
            return self.get_items(tree, test)
        return None

    def parse_json(self, json_output):
        try:
            data = json_output.read()
            try:
                tree = json.loads(str(data, 'utf-8'))
            except Exception:
                tree = json.loads(data)
        except Exception:
            msg = 'Invalid format'
            raise ValueError(msg)
        return tree

    def get_items(self, tree, test):
        items = {}
        scanner = tree.get('scan', {}).get('scanner', {})
        for node in tree['vulnerabilities']:
            item = self.get_item(node, test, scanner)
            if item:
                items[item.unique_id_from_tool] = item
        return list(items.values())

    def get_item(self, vuln, test, scan):
        unique_id_from_tool = (vuln['id'] if ('id' in vuln) else vuln['cve'])
        title = ''
        if ('name' in vuln):
            title = vuln['name']
        elif ('message' in vuln):
            title = vuln['message']
        elif ('description' in vuln):
            title = vuln['description']
        else:
            title = unique_id_from_tool
        description = f'''Scanner: {scan.get('name', 'could not be determined')}
'''
        if ('message' in vuln):
            description += f'''{vuln['message']}
'''
        if ('description' in vuln):
            description += f'''{vuln['description']}
'''
        location = vuln['location']
        file_path = location.get('file', None)
        component_name = None
        component_version = None
        if ('dependency' in location):
            component_version = location['dependency'].get('version', None)
            if ('package' in location['dependency']):
                component_name = location['dependency']['package'].get('name', None)
        severity = vuln['severity']
        if (severity in {'Undefined', 'Unknown'}):
            title = f'[{severity} severity] {title}'
            severity = 'Info'
        scanner_confidence = False
        mitigation = ''
        if ('solution' in vuln):
            mitigation = vuln['solution']
        cwe = None
        vulnerability_id = None
        references = ''
        if ('identifiers' in vuln):
            for identifier in vuln['identifiers']:
                if (identifier['type'].lower() == 'cwe'):
                    cwe = identifier['value']
                elif (identifier['type'].lower() == 'cve'):
                    vulnerability_id = identifier['value']
                else:
                    references += f'''Identifier type: {identifier['type']}
'''
                    references += f'''Name: {identifier['name']}
'''
                    references += f'''Value: {identifier['value']}
'''
                    if ('url' in identifier):
                        references += f'''URL: {identifier['url']}
'''
                    references += '\n'
        finding = Finding(title=(f'{vulnerability_id}: {title}' if vulnerability_id else title), test=test, description=description, severity=severity, scanner_confidence=scanner_confidence, mitigation=mitigation, unique_id_from_tool=unique_id_from_tool, references=references, file_path=file_path, component_name=component_name, component_version=component_version, cwe=cwe, static_finding=True, dynamic_finding=False)
        if vulnerability_id:
            finding.unsaved_vulnerability_ids = [vulnerability_id]
        return finding
