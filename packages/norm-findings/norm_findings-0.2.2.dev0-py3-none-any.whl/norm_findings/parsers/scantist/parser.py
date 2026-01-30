# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding

class ScantistParser():
    '\n    Scantist Parser: Scantist does a deep scan of source code and binaries for vulnerabilities and has reports\n    following three main categories\n    - Components (primary components from dependency graph)\n    - Vulnerabilities (Security Issues)\n    - Compliance (policies and its violations)\n\n    This parser primarily focuses on Vulnerability report and the risks identified in JSON format.\n    @todo: other format will be available soon.\n\n    Website: https://scantist.com/\n    '

    def get_scan_types(self):
        return ['Scantist Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Scantist Dependency Scanning Report vulnerabilities in JSON format.'

    def get_findings(self, scan_file, test):
        tree = json.load(scan_file)
        return self.get_items(tree, test)

    def get_items(self, tree, test):
        '\n        Tree list: input tree list of all the vulnerability findings\n        test:\n        : purpose: parses input rawto extract dojo\n        '

        def get_findings(vuln, test):
            '\n            Vuln : input vulnerable node\n            test :\n            '
            vulnerability_id = vuln.get('Public ID')
            cwe = 1035
            component_name = vuln.get('Library')
            component_version = vuln.get('Library Version')
            title = ((vulnerability_id + '|') + component_name)
            description = vuln.get('Description')
            file_path = vuln.get('File Path', '')
            severity = vuln.get('Score', 'Info')
            mitigation = vuln.get('Patched Version')
            finding = Finding(title=title, test=test, description=description, severity=severity, cwe=cwe, mitigation=mitigation, references=vuln.get('references'), file_path=file_path, component_name=component_name, component_version=component_version, severity_justification=vuln.get('severity_justification'), dynamic_finding=True)
            if vulnerability_id:
                finding.unsaved_vulnerability_ids = [vulnerability_id]
            return finding
        items = {}
        for node in tree:
            item = get_findings(node, test)
            if item:
                hash_key = hashlib.md5((node.get('Public ID').encode('utf-8') + node.get('Library').encode('utf-8')), usedforsecurity=False).hexdigest()
                items[hash_key] = get_findings(node, test)
        return list(items.values())
