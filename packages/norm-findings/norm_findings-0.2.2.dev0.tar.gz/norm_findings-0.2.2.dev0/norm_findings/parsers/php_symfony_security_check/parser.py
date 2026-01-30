# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class PhpSymfonySecurityCheckParser():

    def get_scan_types(self):
        return ['PHP Symfony Security Check']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import results from the PHP Symfony Security Checker by Sensioslabs.'

    def get_findings(self, scan_file, test):
        tree = self.parse_json(scan_file)
        return self.get_items(tree, test)

    def parse_json(self, json_file):
        if (json_file is None):
            return None
        try:
            data = json_file.read()
            try:
                tree = json.loads(str(data, 'utf-8'))
            except Exception:
                tree = json.loads(data)
        except Exception:
            msg = 'Invalid format'
            raise Exception(msg)
        return tree

    def get_items(self, tree, test):
        items = {}
        for (dependency_name, dependency_data) in list(tree.items()):
            advisories = dependency_data.get('advisories')
            dependency_version = dependency_data['version']
            if (dependency_version and dependency_version.startswith('v')):
                dependency_version = dependency_version[1:]
            for advisory in advisories:
                item = get_item(dependency_name, dependency_version, advisory, test)
                unique_key = (str(dependency_name) + str((dependency_data['version'] + str(advisory['cve']))))
                items[unique_key] = item
        return list(items.values())

def get_item(dependency_name, dependency_version, advisory, test):
    finding = Finding(title=((((((dependency_name + ' - ') + '(') + dependency_version) + ', ') + advisory['cve']) + ')'), test=test, severity='Info', description=advisory['title'], cwe=1035, mitigation='upgrade', references=advisory['link'], false_p=False, duplicate=False, out_of_scope=False, mitigated=None, impact='No impact provided', static_finding=True, dynamic_finding=False, component_name=dependency_name, component_version=dependency_version)
    if advisory['cve']:
        finding.unsaved_vulnerability_ids = [advisory['cve']]
    return finding
