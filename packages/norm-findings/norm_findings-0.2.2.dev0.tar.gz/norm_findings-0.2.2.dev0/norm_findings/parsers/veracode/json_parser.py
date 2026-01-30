# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import json
import re
from cvss import CVSS3
from dateutil import parser
from norm_findings.stubs.django.conf import settings
from norm_findings.stubs.models import Endpoint, Finding

class VeracodeJSONParser():
    '\n    This parser is written for Veracode REST Findings.\n\n    API endpoints to use: https://docs.veracode.com/r/c_findings_v2_examples\n\n    Example: curl <endpoint> | jq "{findings}"\n\n    This should convert the format into something like this:\n    {\n        "findings": [\n            {\n                ...\n            },\n            ...\n        ]\n    }\n    '
    severity_mapping = {0: 'Info', 1: 'Info', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}
    exploitability_mapping = {(- 2): 'Very Unlikely', (- 1): 'Unlikely', 0: 'Neutral', 1: 'Likely', 2: 'Very Likely'}
    license_mapping = {0: ('Non OSS', 'Non-OSS indicates that this file could be subject to commercial license terms. If so, you should refer to your applicable license agreement with such vendor for additional information.'), 1: ('Unrecognized', 'Unrecognized indicates that no license was found for the component. However, this does not indicate that there is no risk associated with the license.'), 2: ('Low', 'Low-risk licenses are typically permissive licenses that require you to preserve the copyright and license notices, but allow distribution under different terms without disclosing source code.'), 3: ('Medium', 'Medium-risk licenses are typically weak copyleft licenses that require you to preserve the copyright and license notices, and require distributors to make the source code of the component and any modifications under the same terms.'), 4: ('High', 'High-risk licenses are typically strong copyleft licenses that require you to preserve the copyright and license notices, and require distributors to make the source code of the component and any modifications under the same terms.')}

    def get_findings(self, scan_file, test):
        findings = []
        if scan_file:
            json_data = json.load(scan_file)
            findings += self.get_items(json_data, test)
        return findings

    def get_items(self, tree, test):
        parsed_findings = []
        items = (tree.get('findings', []) or tree.get('_embedded', {}).get('findings', []))
        for vuln in items:
            if (vuln.get('finding_status', {}).get('status', '') == 'CLOSED'):
                continue
            scan_type = vuln.get('scan_type')
            finding_details = vuln.get('finding_details')
            policy_violated = vuln.get('violates_policy')
            finding = self.create_finding_from_details(finding_details, scan_type, policy_violated)
            if (not finding):
                continue
            if (finding_status := vuln.get('finding_status')):
                if settings.USE_FIRST_SEEN:
                    if (first_found_date := finding_status.get('first_found_date')):
                        finding.date = parser.parse(first_found_date)
                elif (last_found_date := finding_status.get('last_found_date')):
                    finding.date = parser.parse(last_found_date)
            finding = self.parse_description(finding, vuln.get('description'), scan_type)
            finding.nb_occurences = vuln.get('count', 1)
            finding.test = test
            parsed_findings.append(finding)
        return parsed_findings

    def create_finding_from_details(self, finding_details, scan_type, policy_violated) -> Finding:
        severity = self.severity_mapping.get(finding_details.get('severity', 1), 1)
        finding = Finding(title=f'{scan_type} Finding', severity=severity, description='### Meta Information\n')
        finding.unsaved_tags = []
        finding.unsaved_endpoints = []
        finding.unsaved_vulnerability_ids = []
        if policy_violated:
            finding.unsaved_tags.append('policy-violation')
        cwe_title = None
        if (cwe_dict := finding_details.get('cwe')):
            cwe_title = cwe_dict.get('name')
            finding.cwe = cwe_dict.get('id')
        if (uncleaned_cvss := finding_details.get('cvss')):
            if isinstance(uncleaned_cvss, str):
                if uncleaned_cvss.startswith(('CVSS:3.1/', 'CVSS:3.0/')):
                    finding.cvssv3 = CVSS3(str(uncleaned_cvss)).clean_vector(output_prefix=True)
                elif (not uncleaned_cvss.startswith('CVSS')):
                    finding.cvssv3 = CVSS3(f'CVSS:3.1/{uncleaned_cvss}').clean_vector(output_prefix=True)
            elif isinstance(uncleaned_cvss, (float, int)):
                finding.cvssv3_score = float(uncleaned_cvss)
        if (scan_type == 'STATIC'):
            return self.add_static_details(finding, finding_details, backup_title=cwe_title)
        if (scan_type == 'DYNAMIC'):
            return self.add_dynamic_details(finding, finding_details, backup_title=cwe_title)
        if (scan_type == 'SCA'):
            return self.add_sca_details(finding, finding_details, backup_title=cwe_title)
        return None

    def add_static_details(self, finding, finding_details, backup_title=None) -> Finding:
        finding.dynamic_finding = False
        finding.static_finding = True
        category_title = (category.get('name') if (category := finding_details.get('finding_category')) else None)
        if category_title:
            finding.title = category_title
        elif backup_title:
            finding.title = backup_title
        if (file_path := finding_details.get('file_path')):
            finding.sast_source_file_path = file_path
            finding.sast_sink_file_path = file_path
            finding.file_path = file_path
        if (file_line_number := finding_details.get('file_line_number')):
            finding.sast_source_line = file_line_number
            finding.sast_sink_line = file_line_number
            finding.line = file_line_number
        if (function_object := finding_details.get('procedure')):
            if isinstance(function_object, str):
                finding.sast_source_object = function_object
                finding.sast_sink_object = function_object
        if (exploitability_score := finding_details.get('exploitability')):
            finding.description += f'''**Exploitability Predication**: {self.exploitability_mapping.get(exploitability_score)}
'''
        if (attack_vector := finding_details.get('attack_vector')):
            finding.description += f'''**Attack Vector**: {attack_vector}
'''
        if (module := finding_details.get('module')):
            finding.description += f'''**Module**: {module}
'''
        return finding

    def add_dynamic_details(self, finding, finding_details, backup_title=None) -> Finding:
        finding.dynamic_finding = True
        finding.static_finding = False
        category_title = (category.get('name') if (category := finding_details.get('finding_category')) else None)
        if category_title:
            finding.title = category_title
        elif backup_title:
            finding.title = backup_title
        if (url := finding_details.get('url')):
            finding.unsaved_endpoints.append(Endpoint.from_uri(url))
        else:
            host = finding_details.get('hostname')
            port = finding_details.get('port')
            path = finding_details.get('path')
            finding.unsaved_endpoints.append(Endpoint(host=host, port=port, path=path))
        if (plugin := finding_details.get('plugin')):
            finding.description += f'''**Plugin**: {plugin}
'''
        if (attack_vector := finding_details.get('attack_vector')):
            finding.description += f'''**Attack Vector**: {attack_vector}
'''
        if (vulnerable_parameter := finding_details.get('vulnerable_parameter')):
            finding.description += f'''**Vulnerable Parameter**: {vulnerable_parameter}
'''
        if (discovered_by_vsa := finding_details.get('discovered_by_vsa')):
            if bool(discovered_by_vsa):
                finding.description += '**Note**: This finding was discovered by Virtual Scan Appliance\n'
        return finding

    def add_sca_details(self, finding, finding_details, backup_title=None) -> Finding:
        finding.dynamic_finding = False
        finding.static_finding = False
        finding.title = backup_title
        vuln_id = None
        if (cve_dict := finding_details.get('cve')):
            vuln_id = cve_dict.get('name')
            finding.unsaved_vulnerability_ids.append(vuln_id)
            if (not finding.cvssv3):
                if (cvss_vector := cve_dict.get('cvss3', {}).get('vector')):
                    finding.cvssv3 = CVSS3(f'CVSS:3.1/{cvss_vector}').clean_vector(output_prefix=True)
        if (product_id := finding_details.get('product_id')):
            finding.description += f'''**Product ID**: {product_id}
'''
        if (component_id := finding_details.get('component_id')):
            finding.description += f'''**Component ID**: {component_id}
'''
        if (language := finding_details.get('language')):
            finding.description += f'''**Language**: {language}
'''
        if (component_paths := finding_details.get('component_path', [])):
            component_paths_markdown = '#### Component Locations\n'
            for path in component_paths:
                component_paths_markdown += f'''- {path.get('path')}
'''
            if (component_paths_markdown != '#### Component Locations\n'):
                finding.description += component_paths_markdown
        if (licenses := finding_details.get('licenses', [])):
            license_markdown = '#### Licenses\n'
            for lic in licenses:
                license_name = lic.get('license_id')
                license_details = self.license_mapping.get(int(lic.get('risk_rating', 5)))
                license_markdown += f'''- {license_name}: {license_details[0]}
    - {license_details[1]}
'''
            if (license_markdown != '#### Licenses\n'):
                finding.description += license_markdown
        if (component_name := finding_details.get('component_filename')):
            if (component_version := finding_details.get('version')):
                finding.component_version = component_version
            finding.component_name = component_name.replace(finding.component_version, '')
            finding.component_name = finding.component_name.replace('-.', '.').replace('_.', '.')
            if finding.component_name.endswith(('-', '_')):
                finding.component_name = finding.component_name[:(- 1)]
        if (not finding.title):
            finding.title = f'{finding.component_name} - {vuln_id}'
        return finding

    def parse_description(self, finding, description_body, scan_type) -> Finding:
        if (scan_type == 'STATIC'):
            sections = description_body.split('<span>')
            sections = [section.replace('</span>', '').strip() for section in sections if (len(section) > 0)]
            if (len(sections) > 0):
                finding.description += f'''### Details
{sections[0]}'''
            if ((len(sections) > 1) and ('References:' not in sections[1])):
                finding.mitigation = sections[1]
            elif ((len(sections) > 1) and ('References:' in sections[1])):
                finding.references = self.parse_references(sections[1])
            if ((len(sections) > 2) and ('References:' in sections[2])):
                finding.references = self.parse_references(sections[2])
        elif (scan_type == 'DYNAMIC'):
            sections = description_body.split('<span>')
            sections = [section.replace('</span>', '').strip() for section in sections if (len(section) > 0)]
            if (len(sections) > 0):
                finding.description += f'''### Details
{sections[0]}'''
            if ((len(sections) > 1) and ('<a href' not in sections[1])):
                finding.mitigation = sections[1]
            elif ((len(sections) > 1) and ('<a href' in sections[1])):
                finding.references = self.parse_references(sections[1])
            if ((len(sections) > 2) and ('<a href' in sections[2])):
                finding.references = self.parse_references(sections[2])
        elif (scan_type == 'SCA'):
            finding.description += f'''### Details
{description_body}'''
        return finding

    def parse_references(self, text) -> str:
        text = text.replace('References: ', '')
        sections = text.split('<a ')
        sections = [section.strip() for section in sections if (len(section) > 0)]
        regex_search = 'href=\\"(.*)\\">(.*)</a>'
        references = [matches.groups() for reference in sections if (matches := re.search(regex_search, reference))]
        reference_string = ''
        for reference in references:
            link = None
            label = None
            if (len(reference) > 0):
                link = reference[0]
            if (len(reference) > 1):
                label = reference[1]
            if (link and label):
                reference_string += f'''- [{label}]({link})
'''
            elif (link and (not label)):
                reference_string += f'''- {link}
'''
        return reference_string
