# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class OSVScannerParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the OSV Parser.\n\n        Fields:\n        - title: Created from vulnerability id and package name.\n        - description: Custom description made from: vulnerability, source_type, & package_ecosystem.\n        - severity: Set to severity from OSV Scanner that has been translated into Defect Dojo format.\n        - static_finding: Set to true.\n        - dynamic_finding: Set to false.\n        - component_name: Set to package name from OSV Scanner.\n        - component_version: Set to package version from OSV Scanner.\n        - cwe: Set to cwe outputted from OSV Scanner.\n        - file_path: Set to source path from OSV Scanner.\n        '
        return ['title', 'description', 'severity', 'static_finding', 'dynamic_finding', 'component_name', 'component_version', 'cwe', 'file_path']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the OSV Parser.\n\n        Fields:\n        - title: Created from vulnerability id and package name.\n        - description: Custom description made from: vulnerability, source_type, & package_ecosystem.\n        - severity: Set to severity from OSV Scanner that has been translated into Defect Dojo format.\n        '
        return ['title', 'description', 'severity']

    def get_scan_types(self):
        return ['OSV Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'OSV Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'OSV scan output can be imported in JSON format (option --format json).'

    def classify_severity(self, severity_input):
        return (('Medium' if (severity_input == 'MODERATE') else severity_input.lower().capitalize()) if severity_input else 'Low')

    def get_findings(self, scan_file, test):
        try:
            data = json.load(scan_file)
        except json.decoder.JSONDecodeError:
            return []
        findings = []
        for result in data.get('results', []):
            source_path = result.get('source', {}).get('path', '')
            source_type = result.get('source', {}).get('type', '')
            for package in result.get('packages', []):
                package_name = package.get('package', {}).get('name')
                package_version = package.get('package', {}).get('version')
                package_ecosystem = package.get('package', {}).get('ecosystem', '')
                for vulnerability in package.get('vulnerabilities', []):
                    vulnerabilityid = vulnerability.get('id', '')
                    vulnerabilitysummary = vulnerability.get('summary', '')
                    vulnerabilitydetails = vulnerability.get('details', '')
                    vulnerabilitypackagepurl = ''
                    cwe = None
                    mitigations_by_type = {}
                    if ((affected := vulnerability.get('affected')) is not None):
                        if (len(affected) > 0):
                            if (vulnerabilitypackage := affected[0].get('package', '')):
                                vulnerabilitypackagepurl = vulnerabilitypackage.get('purl', '')
                            if ((cwe := affected[0].get('database_specific', {}).get('cwes', None)) is not None):
                                cwe = cwe[0]['cweId']
                            ranges = affected[0].get('ranges', [])
                            for range_item in ranges:
                                range_type = range_item.get('type', '')
                                repo_url = range_item.get('repo', '')
                                for event in range_item.get('events', []):
                                    if ('fixed' in event):
                                        fixed_value = event['fixed']
                                        if ((range_type == 'GIT') and repo_url):
                                            formatted_value = f'{repo_url}/commit/{fixed_value}'
                                        else:
                                            formatted_value = fixed_value
                                        if (range_type not in mitigations_by_type):
                                            mitigations_by_type[range_type] = []
                                        mitigations_by_type[range_type].append(formatted_value)
                    mitigation_text = None
                    if mitigations_by_type:
                        mitigation_text = '**Upgrade to versions**:\n'
                        for (typ, versions) in mitigations_by_type.items():
                            mitigation_text += f'''	{typ} :
'''
                            for version in versions:
                                mitigation_text += f'''		- {version}
'''
                    reference = ''
                    for ref in vulnerability.get('references', []):
                        reference += (ref.get('url') + '\n')
                    description = (vulnerabilitysummary + '\n')
                    description += f'''**Source type**: {source_type}
'''
                    description += f'''**Package ecosystem**: {package_ecosystem}
'''
                    description += f'''**Vulnerability details**: {vulnerabilitydetails}
'''
                    description += f'''**Vulnerability package purl**: {vulnerabilitypackagepurl}
'''
                    sev = vulnerability.get('database_specific', {}).get('severity', '')
                    finding = Finding(title=f'{vulnerabilityid}_{package_name}', test=test, description=description, severity=self.classify_severity(sev), static_finding=True, dynamic_finding=False, component_name=package_name, component_version=package_version, cwe=cwe, file_path=source_path, references=reference)
                    if mitigation_text:
                        finding.mitigation = mitigation_text
                    if vulnerabilityid:
                        finding.unsaved_vulnerability_ids = [vulnerabilityid]
                    findings.append(finding)
        return findings
