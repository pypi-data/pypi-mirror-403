# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding
NEUVECTOR_SCAN_NAME = 'NeuVector (compliance)'

def parse(json_output, test):
    tree = parse_json(json_output)
    items = []
    if tree:
        items = list(get_items(tree, test))
    return items

def parse_json(json_output):
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

def get_items(tree, test):
    items = {}
    testsTree = None
    testsTree = (tree.get('report').get('checks', []) if ('report' in tree) else tree.get('items', []))
    for node in testsTree:
        item = get_item(node, test)
        unique_key = (((node.get('type') + node.get('category')) + node.get('test_number')) + node.get('description'))
        unique_key = hashlib.md5(unique_key.encode('utf-8'), usedforsecurity=False).hexdigest()
        items[unique_key] = item
    return list(items.values())

def get_item(node, test):
    if ('test_number' not in node):
        return None
    if ('category' not in node):
        return None
    if ('description' not in node):
        return None
    if ('level' not in node):
        return None
    test_number = node.get('test_number')
    test_description = node.get('description').rstrip()
    title = ((test_number + ' - ') + test_description)
    test_severity = node.get('level')
    severity = convert_severity(test_severity)
    mitigation = node.get('remediation', '').rstrip()
    category = node.get('category')
    vuln_id_from_tool = ((category + '_') + test_number)
    test_profile = node.get('profile', 'profile unknown')
    full_description = f'''{test_number} ({category}), {test_profile}:
'''
    full_description += f'''{test_description}
'''
    full_description += f'''Audit: {test_severity}
'''
    if ('evidence' in node):
        full_description += 'Evidence:\n{}\n'.format(node.get('evidence'))
    if ('location' in node):
        full_description += 'Location:\n{}\n'.format(node.get('location'))
    full_description += f'''Mitigation:
{mitigation}
'''
    tags = node.get('tags', [])
    if (len(tags) > 0):
        full_description += 'Tags:\n'
        for t in tags:
            full_description += f'''{str(t).rstrip()}
'''
    messages = node.get('message', [])
    if (len(messages) > 0):
        full_description += 'Messages:\n'
        for m in messages:
            full_description += f'''{str(m).rstrip()}
'''
    return Finding(title=title, test=test, description=full_description, severity=severity, mitigation=mitigation, vuln_id_from_tool=vuln_id_from_tool, static_finding=True, dynamic_finding=False)

def convert_severity(severity):
    if (severity.lower() == 'high'):
        return 'High'
    if (severity.lower() == 'warn'):
        return 'Medium'
    if (severity.lower() == 'info'):
        return 'Low'
    if (severity.lower() in {'pass', 'note', 'error'}):
        return 'Info'
    return severity.title()

class NeuVectorComplianceParser():

    def get_scan_types(self):
        return [NEUVECTOR_SCAN_NAME]

    def get_label_for_scan_types(self, scan_type):
        return NEUVECTOR_SCAN_NAME

    def get_description_for_scan_types(self, scan_type):
        return 'Imports compliance scans returned by REST API.'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return []
        if scan_file.name.lower().endswith('.json'):
            return parse(scan_file, test)
        msg = 'Unknown File Format'
        raise ValueError(msg)
