# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.sarif.parser import SarifParser

class SnykCodeParser(SarifParser):

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Snyk Code Parser\n\n        Fields:\n        - title: Made using the title from Snyk Code scanner.\n        - severity: Set to severity from Snyk Code Scanner converted to Defect Dojo format.\n        - severity_justification: Made using severity and CVSS score from Snyk Code Parser.\n        - description: Made by combining package name, version, vulnerable version(s), and description from Snyk Code Scanner.\n        - mitigation: Set to a string and is added on if more context is available.\n        - component_name: Set to component_name from Snyk Code Scanner.\n        - component_version: Set to version from Snyk Code Scanner.\n        - false_p: Set to false.\n        - duplicate: Set to false.\n        - out_of_scope: Set to false.\n        - impact: Set to same value as severity.\n        - static_finding: Set to true.\n        - dynamic_finding: Set to false.\n        - file_path: Set to from value in the Snyk Code scanner output.\n        - vuln_id_from_tool: Set to id from Snyk Code scanner.\n        - cvssv3: Set to cvssv3 from Snyk Code scanner if available.\n        - cwe: Set to the cwe values outputted from Burp Scanner.\n        '
        return ['title', 'severity', 'severity_justification', 'description', 'mitigation', 'component_name', 'component_version', 'false_p', 'duplicate', 'out_of_scope', 'impact', 'static_finding', 'dynamic_finding', 'file_path', 'vuln_id_from_tool', 'cvssv3', 'cwe']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of dedupe fields used in the Snyk Code Parser\n\n        Fields:\n        - vuln_id_from_tool: Set to id from Snyk Code scanner.\n        - file_path: Set to from value in the Snyk Code scanner output.\n        '
        return ['vuln_id_from_tool', 'file_path']

    def get_scan_types(self):
        return ['Snyk Code Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Snyk Code Scan output can be imported in SARIF JSON format. Generate SARIF reports using: snyk code test --sarif'

    def get_finding_title(self, result, rule, location):
        'Get custom title for Snyk Code with ruleId + file path format'
        rule_id = result.get('ruleId', '')
        file_path = ''
        if location:
            phys_loc = location.get('physicalLocation', {})
            artifact_loc = phys_loc.get('artifactLocation', {})
            file_path = artifact_loc.get('uri', '')
        return (f'{rule_id}_{file_path}' if (rule_id and file_path) else rule_id)

    def get_finding_description(self, result, rule, location):
        'Custom description formatting for Snyk Code SARIF reports'
        props = result.get('properties', {})
        rule_id = result.get('ruleId', '')
        description_parts = [f'**ruleId**: {rule_id}', f"**ruleIndex**: {result.get('ruleIndex', '')}", f"**message**: {result.get('message', {}).get('text', '')}", f"**score**: {props.get('priorityScore', 0)}", f"**isAutofixable**: {props.get('isAutofixable', False)}"]
        if location:
            phys_loc = location.get('physicalLocation', {})
            artifact_loc = phys_loc.get('artifactLocation', {})
            region = phys_loc.get('region', {})
            if artifact_loc.get('uri'):
                description_parts.append(f"**uri**: {artifact_loc.get('uri', '')}")
            if artifact_loc.get('uriBaseId'):
                description_parts.append(f"**uriBaseId**: {artifact_loc.get('uriBaseId', '')}")
            if region.get('startLine'):
                description_parts.append(f"**startLine**: {region.get('startLine', '')}")
            if region.get('endLine'):
                description_parts.append(f"**endLine**: {region.get('endLine', '')}")
            if region.get('startColumn'):
                description_parts.append(f"**startColumn**: {region.get('startColumn', '')}")
            if region.get('endColumn'):
                description_parts.append(f"**endColumn**: {region.get('endColumn', '')}")
        return '\n'.join(description_parts)

    def customize_finding(self, finding, result, rule, location):
        'Customize SARIF finding for Snyk Code specific formatting'
        props = result.get('properties', {})
        score = props.get('priorityScore', 0)
        if (score <= 399):
            finding.severity = 'Low'
        elif (score <= 699):
            finding.severity = 'Medium'
        elif (score <= 899):
            finding.severity = 'High'
        else:
            finding.severity = 'Critical'
