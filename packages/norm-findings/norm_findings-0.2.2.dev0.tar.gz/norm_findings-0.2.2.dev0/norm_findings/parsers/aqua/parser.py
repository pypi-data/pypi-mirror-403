# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding
from norm_findings.stubs.utils import parse_cvss_data

class AquaParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Aqua Parser.\n\n        Fields:\n        - title: Made by combining cve, resource_name, and resource_version.\n        - severity: Severity converted from Aqua format into Defect Dojo format.\n        - severity_justification: Set to justification returned by Aqua scanner.\n        - cvssv3: Defined based on the output of the Aqua Scanner.\n        - description: Set to description returned from Aqua Scanner. If no description is present set to "no description".\n        - mitigation: Set to fix_version returned from Aqua Scanner.\n        - references: Set to url returned from Aqua Scanner.\n        - component_name: Set to name returned from Aqua Scanner.\n        - component_version: Set to version returned from Aqua Scanner.\n        - impact: Set to same value as severity.\n        - epss_score: Set to epss_score returned from scanner if it exists.\n        - epss_percentile: Set to epss_percentile returned from scanner if it exists.\n        '
        return ['title', 'severity', 'severity_justification', 'cvssv3', 'description', 'mitigation', 'references', 'component_name', 'component_version', 'impact', 'epss_score', 'epss_percentile']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Aqua Parser.\n\n        Fields:\n        - severity: Severity converted from Aqua format into Defect Dojo format.\n        - component_name: Set to name returned from Aqua Scanner.\n        - component_version: Set to version returned from Aqua Scanner.\n\n        #NOTE: vulnerability_ids is not provided by parser\n        '
        return ['severity', 'component_name', 'component_version']

    def get_scan_types(self):
        return ['Aqua Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Aqua Scan'

    def get_description_for_scan_types(self, scan_type):
        return ''

    def get_findings(self, scan_file, test):
        tree = json.load(scan_file)
        self.items = {}
        if isinstance(tree, list):
            vulnerabilitytree = (tree[0]['results']['resources'] if tree else [])
            self.vulnerability_tree(vulnerabilitytree, test)
        elif ('resources' in tree):
            vulnerabilitytree = tree['resources']
            self.vulnerability_tree(vulnerabilitytree, test)
        elif ('result' in tree):
            resulttree = tree['result']
            for vuln in resulttree:
                resource = vuln.get('resource')
                item = self.get_item(resource, vuln, test)
                unique_key = ((resource.get('cpe') + vuln.get('name', 'None')) + resource.get('path', 'None'))
                self.items[unique_key] = item
        elif ('cves' in tree):
            for cve in tree['cves']:
                unique_key = (cve.get('file') + cve.get('name'))
                self.items[unique_key] = self.get_item_v2(cve, test)
        return list(self.items.values())

    def vulnerability_tree(self, vulnerabilitytree, test):
        for node in vulnerabilitytree:
            resource = node.get('resource')
            vulnerabilities = node.get('vulnerabilities', [])
            sensitive_items = resource.get('sensitive_items', [])
            if (vulnerabilities is None):
                vulnerabilities = []
            for vuln in vulnerabilities:
                item = self.get_item(resource, vuln, test)
                unique_key = ((resource.get('cpe') + vuln.get('name', 'None')) + resource.get('path', 'None'))
                self.items[unique_key] = item
            if (sensitive_items is None):
                sensitive_items = []
            for sensitive_item in sensitive_items:
                item = self.get_item_sensitive_data(resource, sensitive_item, test)
                unique_key = ((resource.get('cpe') + resource.get('path', 'None')) + str(sensitive_item))
                self.items[unique_key] = item

    def get_item(self, resource, vuln, test):
        resource_name = resource.get('name', resource.get('path'))
        resource_version = resource.get('version', 'No version')
        vulnerability_id = vuln.get('name', 'No CVE')
        fix_available = False
        fix_version = vuln.get('fix_version', None)
        if (fix_version is not None):
            fix_available = True
        description = (vuln.get('description', 'No description.') + '\n')
        if resource.get('path'):
            description += (('**Path:** ' + resource.get('path')) + '\n')
        cvssv3 = None
        url = ''
        if ('nvd_url' in vuln):
            url += '\n{}'.format(vuln.get('nvd_url'))
        if ('vendor_url' in vuln):
            url += '\n{}'.format(vuln.get('vendor_url'))
        score = None
        severity_justification = ''
        used_for_classification = ''
        if ('aqua_severity' in vuln):
            if (score is None):
                score = vuln.get('aqua_severity')
                used_for_classification = f'''Aqua severity ({score}) used for classification.
'''
            severity_justification += '\nAqua severity classification: {}'.format(vuln.get('aqua_severity_classification'))
            severity_justification += '\nAqua scoring system: {}'.format(vuln.get('aqua_scoring_system'))
            if ('nvd_score_v3' in vuln):
                cvssv3 = vuln.get('nvd_vectors_v3')
        if ('aqua_score' in vuln):
            if (score is None):
                score = vuln.get('aqua_score')
                used_for_classification = f'''Aqua score ({score}) used for classification.
'''
            severity_justification += '\nAqua score: {}'.format(vuln.get('aqua_score'))
        if ('vendor_score' in vuln):
            if (score is None):
                score = vuln.get('vendor_score')
                used_for_classification = f'''Vendor score ({score}) used for classification.
'''
            severity_justification += '\nVendor score: {}'.format(vuln.get('vendor_score'))
        if ('nvd_score_v3' in vuln):
            if (score is None):
                score = vuln.get('nvd_score_v3')
                used_for_classification = f'''NVD score v3 ({score}) used for classification.
'''
            severity_justification += '\nNVD v3 vectors: {}'.format(vuln.get('nvd_vectors_v3'))
            cvssv3 = vuln.get('nvd_vectors_v3')
        if ('nvd_score' in vuln):
            if (score is None):
                score = vuln.get('nvd_score')
                used_for_classification = f'''NVD score v2 ({score}) used for classification.
'''
            severity_justification += '\nNVD v2 vectors: {}'.format(vuln.get('nvd_vectors'))
        severity_justification += f'''
{used_for_classification}'''
        severity = self.severity_of(score)
        finding = Finding(title=(((((vulnerability_id + ' - ') + resource_name) + ' (') + resource_version) + ') '), test=test, severity=severity, severity_justification=severity_justification, cwe=0, description=description.strip(), mitigation=fix_version, references=url, component_name=resource.get('name'), component_version=resource.get('version'), impact=severity, fix_available=fix_available)
        cvss_data = parse_cvss_data(cvssv3)
        if cvss_data:
            finding.cvssv3 = cvss_data.get('cvssv3')
            finding.cvssv3_score = cvss_data.get('cvssv3_score')
        if (vulnerability_id != 'No CVE'):
            finding.unsaved_vulnerability_ids = [vulnerability_id]
        if vuln.get('epss_score'):
            finding.epss_score = vuln.get('epss_score')
        if vuln.get('epss_percentile'):
            finding.epss_percentile = vuln.get('epss_percentile')
        return finding

    def get_item_v2(self, item, test):
        vulnerability_id = item['name']
        file_path = item['file']
        url = item.get('url')
        severity = self.severity_of(float(item['score']))
        description = item.get('description')
        solution = item.get('solution')
        fix_available = False
        fix_version = item.get('fix_version', None)
        if (fix_version is not None):
            fix_available = True
        if solution:
            mitigation = solution
        elif fix_version:
            mitigation = ('Upgrade to ' + str(fix_version))
        else:
            mitigation = 'No known mitigation'
        finding = Finding(title=((str(vulnerability_id) + ': ') + str(file_path)), description=description, url=url, cwe=0, test=test, severity=severity, impact=severity, mitigation=mitigation, fix_available=fix_available)
        finding.unsaved_vulnerability_ids = [vulnerability_id]
        return finding

    def get_item_sensitive_data(self, resource, sensitive_item, test):
        resource_name = resource.get('name', 'None')
        resource_path = resource.get('path', 'None')
        vulnerability_id = resource_name
        description = (('**Senstive Item:** ' + sensitive_item) + '\n')
        description += (('**Layer:** ' + resource.get('layer', 'None')) + '\n')
        description += (('**Layer_Digest:** ' + resource.get('layer_digest', 'None')) + '\n')
        description += (('**Path:** ' + resource.get('path', 'None')) + '\n')
        finding = Finding(title=(((((vulnerability_id + ' - ') + resource_name) + ' (') + resource_path) + ') '), test=test, severity='Info', description=description.strip(), component_name=resource.get('name'))
        if (vulnerability_id != 'No CVE'):
            finding.unsaved_vulnerability_ids = [vulnerability_id]
        return finding

    def severity_of(self, score):
        if isinstance(score, str):
            if (score == 'high'):
                return 'High'
            if (score == 'medium'):
                return 'Medium'
            if (score == 'low'):
                return 'Low'
            if (score == 'negligible'):
                return 'Info'
            return 'Critical'
        if (score == 0):
            return 'Info'
        if (score < 4):
            return 'Low'
        if (4.0 < score < 7.0):
            return 'Medium'
        if (7.0 < score < 9.0):
            return 'High'
        return 'Critical'
