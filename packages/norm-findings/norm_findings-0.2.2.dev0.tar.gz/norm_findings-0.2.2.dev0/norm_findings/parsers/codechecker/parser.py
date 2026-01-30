# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding

class CodeCheckerParser():

    def get_scan_types(self):
        return ['Codechecker Report native']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Codechecker Report in native JSON format.'

    def get_requires_file(self, scan_type):
        return True

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return None
        tree = self.parse_json(scan_file)
        if tree:
            return self.get_items(tree)
        return None

    def parse_json(self, json_output):
        data = json_output.read()
        return json.loads(data)

    def get_items(self, tree):
        items = {}
        for node in tree['reports']:
            item = get_item(node)
            if item:
                items[item.unique_id_from_tool] = item
        return list(items.values())

def get_item(vuln):
    description = 'Analyzer name: {}\n'.format(vuln['analyzer_name'])
    description += 'Category name: {}\n'.format(vuln['category'])
    description += 'Checker name: {}\n'.format(vuln['checker_name'])
    if ('type' in vuln):
        vuln_type = vuln.get('type', 'None')
        if (vuln_type != 'None'):
            description += f'''Type: {vuln_type}
'''
    if ('message' in vuln):
        description += '{}\n'.format(vuln['message'])
    location = vuln['file']
    file_path = location.get('path', None)
    if file_path:
        description += f'''File path: {file_path}
'''
    line = vuln.get('line', None)
    column = vuln.get('column', None)
    if ((line is not None) and (column is not None)):
        description += f'''Location in file: line {line}, column {column}
'''
    sast_source_line = line
    severity = get_mapped_severity(vuln.get('severity', 'UNSPECIFIED'))
    review_status = vuln.get('review_status', 'unreviewed')
    verified = (review_status == 'confirmed')
    risk_accepted = (review_status == 'intentional')
    false_positive = (review_status in {'false_positive', 'suppressed'})
    active = ((not false_positive) and (not risk_accepted))
    unique_id = (((vuln['report_hash'] + '.') + vuln['analyzer_result_file_path']) + description)
    unique_id_from_tool = hashlib.sha256(unique_id.encode()).hexdigest()
    title = ''
    if ('checker_name' in vuln):
        title = vuln['checker_name']
    elif ('message' in vuln):
        title = vuln['message']
    else:
        title = unique_id_from_tool
    finding = Finding(title=title, description=description, severity=severity, unique_id_from_tool=unique_id_from_tool, file_path=file_path, line=line, active=active, verified=verified, risk_accepted=risk_accepted, false_p=false_positive, sast_source_file_path=file_path, sast_source_line=sast_source_line, static_finding=True, dynamic_finding=False)
    finding.unsaved_tags = [vuln['analyzer_name']]
    return finding

def get_mapped_severity(severity):
    switcher = {'CRITICAL': 'Critical', 'HIGH': 'High', 'MEDIUM': 'Medium', 'LOW': 'Low', 'STYLE': 'Info', 'UNSPECIFIED': 'Info'}
    return switcher.get(severity.upper())
