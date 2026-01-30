# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import io
import json
from cvss.cvss3 import CVSS3
from norm_findings.stubs.models import Finding
from norm_findings.parsers.snyk_code.parser import SnykCodeParser

class SnykParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Snyk Parser.\n\n        Fields:\n        - title: Made from vulnerability and vulnerability title.\n        - severity: Set to cvssScore from Snyk Scanner and translated into DefectDojo format.\n        - severity_justification: Made from combining data about the cvssScore.\n        - description: Made from details on vulnerability.\n        - mitigation: Made from combining data about the cvssScore.\n        - component_name: Set to vulnerability packageName from Snyk Parser.\n        - component_version: Set to vulnerability version from Snyk Parser.\n        - false_p: Set to false.\n        - duplicate: Set to false.\n        - out_of_scope: Set to false.\n        - impact: Set to value of severity.\n        - static_finding: Set to true.\n        - dynamic_finding: Set to false.\n        - file_path: Made by Snyk parser while removing versions.\n        - vuln_id_from_tool: Set to vulnerability id from Snyk Scanner.\n        - cvssv3: Set to cvssv3 from Scanner if present.\n        - epss_score: Set to epss_score from Scanner if "epssDetails" are present.\n        - epss_percentile: Set to epss_percentile from Scanner if "epssDetails" are present.\n        - cwe: Set to cwe from scanner if present.\n        '
        return ['title', 'severity', 'severity_justification', 'description', 'mitigation', 'component_name', 'component_version', 'false_p', 'duplicate', 'out_of_scope', 'impact', 'static_finding', 'dynamic_finding', 'file_path', 'vuln_id_from_tool', 'cvssv3', 'epss_score', 'epss_percentile', 'cwe']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Snyk Parser.\n\n        Fields:\n        - vuln_id_from_tool: Set to vulnerability id from Snyk Scanner.\n        - file_path: Made by Snyk parser while removing versions.\n        - component_name: Set to vulnerability packageName from Snyk Parser.\n        - component_version: Set to vulnerability version from Snyk Parser.\n        '
        return ['vuln_id_from_tool', 'file_path', 'component_name', 'component_version']

    def get_scan_types(self):
        return ['Snyk Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Snyk output file (snyk test --json > snyk.json) can be imported in JSON format. SARIF format is automatically delegated to the Snyk Code parser.'

    def get_findings(self, scan_file, test):
        reportTree = self.parse_json(scan_file)
        if isinstance(reportTree, list):
            temp = []
            for moduleTree in reportTree:
                temp += self.process_tree(moduleTree, test)
            return temp
        return self.process_tree(reportTree, test)

    def process_tree(self, tree, test):
        return (list(self.get_items(tree, test)) if tree else [])

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
        items = []
        if ('vulnerabilities' in tree):
            target_file = tree.get('displayTargetFile', None)
            upgrades = tree.get('remediation', {}).get('upgrade', None)
            vulnerabilityTree = tree['vulnerabilities']
            for node in vulnerabilityTree:
                item = self.get_item(node, test, target_file=target_file, upgrades=upgrades)
                items.append(item)
            return items
        if (('runs' in tree) and tree['runs'][0].get('results')):
            snyk_code_parser = SnykCodeParser()
            json_output = io.StringIO(json.dumps(tree))
            findings = snyk_code_parser.get_findings(json_output, test)
            items.extend(findings)
            return findings
        return []

    def get_item(self, vulnerability, test, target_file=None, upgrades=None):
        if isinstance(vulnerability['semver']['vulnerable'], list):
            vulnerable_versions = ', '.join(vulnerability['semver']['vulnerable'])
        else:
            vulnerable_versions = vulnerability['semver']['vulnerable']
        if ('cvssScore' in vulnerability):
            if (vulnerability['cvssScore'] is None):
                severity = vulnerability['severity'].title()
            elif (vulnerability['cvssScore'] <= 3.9):
                severity = 'Low'
            elif ((vulnerability['cvssScore'] >= 4.0) and (vulnerability['cvssScore'] <= 6.9)):
                severity = 'Medium'
            elif ((vulnerability['cvssScore'] >= 7.0) and (vulnerability['cvssScore'] <= 8.9)):
                severity = 'High'
            else:
                severity = 'Critical'
        else:
            severity = vulnerability['severity'].title()
        vulnPath = ''
        for (index, item) in enumerate(vulnerability['from']):
            if (index == 0):
                vulnPath += '@'.join(item.split('@')[0:(- 1)])
            else:
                vulnPath += (' > ' + '@'.join(item.split('@')[0:(- 1)]))
        finding = Finding(title=((vulnerability['from'][0] + ': ') + vulnerability['title']), test=test, severity=severity, severity_justification=((((('Issue severity of: **' + severity) + '** from a base ') + 'CVSS score of: **') + str(vulnerability.get('cvssScore'))) + '**'), description=((((((((('## Component Details\n - **Vulnerable Package**: ' + vulnerability['packageName']) + '\n- **Current Version**: ') + str(vulnerability['version'])) + '\n- **Vulnerable Version(s)**: ') + vulnerable_versions) + '\n- **Vulnerable Path**: ') + ' > '.join(vulnerability['from'])) + '\n') + vulnerability['description']), mitigation='A fix (if available) will be provided in the description.', component_name=vulnerability['packageName'], component_version=vulnerability['version'], false_p=False, duplicate=False, out_of_scope=False, impact=severity, static_finding=True, dynamic_finding=False, file_path=vulnPath, vuln_id_from_tool=vulnerability['id'])
        finding.unsaved_tags = []
        if vulnerability.get('CVSSv3'):
            finding.cvssv3 = CVSS3(vulnerability['CVSSv3']).clean_vector()
        if (vulnerability.get('epssDetails') is not None):
            finding.epss_score = vulnerability['epssDetails']['probability']
            finding.epss_percentile = vulnerability['epssDetails']['percentile']
        cwe_references = ''
        if ('identifiers' in vulnerability):
            if ('CVE' in vulnerability['identifiers']):
                vulnerability_ids = vulnerability['identifiers']['CVE']
                if vulnerability_ids:
                    finding.unsaved_vulnerability_ids = vulnerability_ids
            if ('CWE' in vulnerability['identifiers']):
                cwes = vulnerability['identifiers']['CWE']
                if cwes:
                    finding.cwe = int(cwes[0].split('-')[1])
                    if (len(vulnerability['identifiers']['CWE']) > 1):
                        cwe_references = ', '.join(cwes)
                else:
                    finding.cwe = 1035
        references = ''
        if ('id' in vulnerability):
            references = '**SNYK ID**: https://app.snyk.io/vuln/{}\n\n'.format(vulnerability['id'])
        if cwe_references:
            references += f'''Several CWEs were reported: 

{cwe_references}
'''
        for item in vulnerability.get('references', []):
            references += (((('**' + item['title']) + '**: ') + item['url']) + '\n')
        finding.references = references
        finding.description = finding.description.strip()
        remediation_index = finding.description.find('## Remediation')
        references_index = finding.description.find('## References')
        if ((remediation_index != (- 1)) and (references_index != (- 1))):
            finding.mitigation = finding.description[remediation_index:references_index]
        if target_file:
            finding.unsaved_tags.append(f'target_file:{target_file}')
            finding.mitigation += f'''
Upgrade Location: {target_file}'''
        if upgrades:
            for (current_pack_version, meta_dict) in upgrades.items():
                upgraded_pack = meta_dict['upgradeTo']
                tertiary_upgrade_list = meta_dict['upgrades']
                if any(((lib.split('@')[0] in finding.mitigation) for lib in tertiary_upgrade_list)):
                    finding.unsaved_tags.append(f'upgrade_to:{upgraded_pack}')
                    finding.mitigation += f'''
Upgrade from {current_pack_version} to {upgraded_pack} to fix this issue, as well as updating the following:
 - '''
                    finding.mitigation += '\n - '.join(tertiary_upgrade_list)
        return finding
