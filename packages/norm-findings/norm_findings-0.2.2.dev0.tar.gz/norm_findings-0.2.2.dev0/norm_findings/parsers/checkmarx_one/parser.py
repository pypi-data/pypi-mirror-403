# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Test, Finding

import datetime
import json
import re
from dateutil import parser
from norm_findings.stubs.django.conf import settings
from norm_findings.stubs.models import Finding, Test

class CheckmarxOneParser():

    def get_scan_types(self):
        return ['Checkmarx One Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Checkmarx One Scan'

    def _parse_date(self, value):
        if isinstance(value, str):
            return parser.parse(value)
        if (isinstance(value, dict) and isinstance(value.get('seconds'), int)):
            return datetime.datetime.fromtimestamp(value.get('seconds'), datetime.timezone.utc)
        return None

    def _parse_cwe(self, cwe):
        if isinstance(cwe, str):
            cwe_num = re.findall('\\d+', cwe)
            if cwe_num:
                return cwe_num[0]
            return None
        if isinstance(cwe, int):
            return cwe
        return None

    def parse_vulnerabilities_from_scan_list(self, test: Test, data: dict) -> list[Finding]:
        findings = []
        cwe_store = data.get('vulnerabilityDetails', [])
        if ((results := data.get('scanResults', {}).get('resultsList')) is not None):
            findings += self.parse_sast_vulnerabilities(test, results, cwe_store)
        if ((results := data.get('iacScanResults', {}).get('technology')) is not None):
            findings += self.parse_iac_vulnerabilities(test, results, cwe_store)
        if ((results := data.get('scaScanResults', {}).get('packages')) is not None):
            findings += self.parse_sca_vulnerabilities(test, results, cwe_store)
        return findings

    def parse_iac_vulnerabilities(self, test: Test, results: list, cwe_store: list) -> list[Finding]:
        findings = []
        for technology in results:
            name = technology.get('name', 'IaC Finding')
            for query in technology.get('queries', []):
                base_finding_details = {'title': f"{name}: {query.get('queryName')}", 'description': f'''{query.get('description')}

**Category**: {query.get('category')}
''', 'test': test}
                for instance in query.get('resultsList'):
                    if settings.USE_FIRST_SEEN:
                        date = self._parse_date(instance.get('firstDetectionDate'))
                    else:
                        date = self._parse_date(instance.get('lastDetectionDate'))
                    instance_details = self.determine_state(instance)
                    instance_details.update(base_finding_details)
                    finding = Finding(severity=instance.get('severity').title(), date=date, file_path=instance.get('fileName'), mitigation=f'''**Actual Value**: {instance.get('actualValue')}
**Expected Value**: {instance.get('expectedValue')}
''', **instance_details)
                    finding.description += f'''**Issue Type**: {instance.get('issueType')}
[View in Checkmarx One]({instance.get('resultViewerLink')})'''
                    finding.unsaved_tags = ['iac']
                    findings.append(finding)
        return findings

    def parse_sca_vulnerabilities(self, test: Test, results: list, cwe_store: list) -> list[Finding]:
        return []

    def parse_sast_vulnerabilities(self, test: Test, results: list, cwe_store: list) -> list[Finding]:

        def get_cwe_store_entry(cwe_store: list, cwe: int) -> dict:
            if (cwe is None):
                return {}
            for entry in cwe_store:
                if (entry.get('cweId', 0) == cwe):
                    return entry
            return {}

        def get_markdown_categories(categories: list) -> str:
            value = ''
            for category in categories:
                value += f'''- {category.get('name')}
'''
                for sub_category in category.get('subCategories', []):
                    value += f'''	- {sub_category}
'''
            return value

        def get_node_snippet(nodes: list) -> str:
            formatted_nodes = [f'''**File Name**: {node.get('fileName')}
**Method**: {node.get('method')}
**Line**: {node.get('line')}
**Code Snippet**: {node.get('code')}
''' for node in nodes]
            return '\n---\n'.join(formatted_nodes)
        findings = []
        for result in results:
            cwe = result.get('cweId')
            cwe_info = get_cwe_store_entry(cwe_store, cwe)
            base_finding_details = {'title': result.get('queryPath', result.get('queryName', 'SAST Finding')).replace('_', ' '), 'description': f'''{result.get('description')}

{cwe_info.get('cause', '')}''', 'references': get_markdown_categories(result.get('categories', [])), 'impact': cwe_info.get('risk', ''), 'mitigation': cwe_info.get('generalRecommendations', ''), 'cwe': cwe, 'test': test}
            for instance in result.get('vulnerabilities'):
                if settings.USE_FIRST_SEEN:
                    date = self._parse_date(instance.get('firstFoundDate'))
                else:
                    date = self._parse_date(instance.get('foundDate'))
                instance_details = self.determine_state(instance)
                instance_details.update(base_finding_details)
                finding = Finding(severity=instance.get('severity').title(), date=date, file_path=instance.get('destinationFileName'), line=instance.get('destinationLine'), **instance_details)
                if (node_snippet := get_node_snippet(instance.get('nodes', []))):
                    finding.description += f'''
---
{node_snippet}'''
                finding.unsaved_tags = ['sast']
                findings.append(finding)
        return findings

    def parse_vulnerabilities(self, test: Test, results: list) -> list[Finding]:
        findings = []
        for result in results:
            result_id = result.get('identifiers')[0].get('value')
            cwe = None
            if ('vulnerabilityDetails' in result):
                cwe = result.get('vulnerabilites').get('cweId')
            severity = result.get('severity')
            locations_uri = result.get('location').get('file')
            locations_startLine = result.get('location').get('start_line')
            locations_endLine = result.get('location').get('end_line')
            finding = Finding(unique_id_from_tool=result_id, file_path=locations_uri, line=locations_startLine, title=((result_id + '_') + locations_uri), test=test, cwe=cwe, severity=severity, description=((((((((((('**id**: ' + str(result_id)) + '\n') + '**uri**: ') + locations_uri) + '\n') + '**startLine**: ') + str(locations_startLine)) + '\n') + '**endLine**: ') + str(locations_endLine)) + '\n'), static_finding=True, dynamic_finding=False, **self.determine_state(result))
            findings.append(finding)
        return findings

    def parse_results(self, test: Test, results: list) -> list[Finding]:
        findings = []
        for vulnerability in results:
            result_type = vulnerability.get('type')
            date = self._parse_date(vulnerability.get('firstFoundAt'))
            cwe = self._parse_cwe(vulnerability.get('vulnerabilityDetails', {}).get('cweId', None))
            finding = None
            if (result_type == 'sast'):
                finding = self.get_results_sast(test, vulnerability)
            elif (result_type == 'kics'):
                finding = self.get_results_kics(test, vulnerability)
            elif (result_type in {'sca', 'sca-container'}):
                finding = self.get_results_sca(test, vulnerability)
            if (finding is not None):
                finding.date = date
                finding.cwe = cwe
                finding.unsaved_tags = [result_type]
                findings.append(finding)
        return findings

    def get_results_sast(self, test: Test, vulnerability: dict) -> Finding:
        description = vulnerability.get('description')
        file_path = vulnerability.get('data').get('nodes')[0].get('fileName')
        unique_id_from_tool = vulnerability.get('id', vulnerability.get('similarityId'))
        if (description is None):
            description = ((vulnerability.get('severity').title() + ' ') + vulnerability.get('data').get('queryName').replace('_', ' '))
        return Finding(description=description, title=description, file_path=file_path, severity=vulnerability.get('severity').title(), test=test, static_finding=True, unique_id_from_tool=unique_id_from_tool, **self.determine_state(vulnerability))

    def get_results_kics(self, test: Test, vulnerability: dict) -> Finding:
        description = vulnerability.get('description')
        file_path = vulnerability.get('data').get('filename', vulnerability.get('data').get('fileName'))
        unique_id_from_tool = vulnerability.get('id', vulnerability.get('similarityId'))
        if (description is None):
            description = ((vulnerability.get('severity').title() + ' ') + vulnerability.get('data').get('queryName').replace('_', ' '))
        return Finding(title=description, description=description, severity=vulnerability.get('severity').title(), file_path=file_path, test=test, static_finding=True, unique_id_from_tool=unique_id_from_tool, **self.determine_state(vulnerability))

    def get_results_sca(self, test: Test, vulnerability: dict) -> Finding:
        description = vulnerability.get('description')
        unique_id_from_tool = vulnerability.get('id', vulnerability.get('similarityId'))
        if (description is None):
            description = ((vulnerability.get('severity').title() + ' ') + vulnerability.get('data').get('queryName').replace('_', ' '))
        finding = Finding(title=description, description=description, severity=vulnerability.get('severity').title(), test=test, static_finding=True, unique_id_from_tool=unique_id_from_tool, **self.determine_state(vulnerability))
        if ((cveId := vulnerability.get('cveId')) is not None):
            finding.unsaved_vulnerability_ids = [cveId]
        return finding

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        findings = []
        if any(((vuln_type in data) for vuln_type in ['scaScanResults', 'iacScanResults', 'scanResults'])):
            findings = self.parse_vulnerabilities_from_scan_list(test, data)
        if ((results := data.get('vulnerabilities', None)) is not None):
            findings = self.parse_vulnerabilities(test, results)
        elif ((results := data.get('results', None)) is not None):
            findings = self.parse_results(test, results)
        return findings

    def determine_state(self, data: dict) -> dict:
        '\n        Determine the state of the findings as set by Checkmarx One docs\n        https://docs.checkmarx.com/en/34965-68516-managing--triaging--vulnerabilities0.html#UUID-bc2397a3-1614-48bc-ff2f-1bc342071c5a_UUID-ad4991d6-161f-f76e-7d04-970f158eff9b\n        '
        state = data.get('state')
        return {'active': (state in {'TO_VERIFY', 'PROPOSED_NOT_EXPLOITABLE', 'CONFIRMED', 'URGENT'}), 'verified': (state in {'NOT_EXPLOITABLE', 'CONFIRMED', 'URGENT'}), 'false_p': (state == 'NOT_EXPLOITABLE'), 'duplicate': False, 'out_of_scope': False}
