# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import hashlib
import json
import logging
import re
from datetime import datetime
from norm_findings.stubs.models import Endpoint, Finding

class WhiteHatSentinelParser():
    '\n    A class to parse WhiteHat Sentinel vulns from the WhiteHat Sentinel API vuln?query_site=[\n    SITE_ID]&format=json&display_attack_vectors=all&display_custom_risk=1&display_risk=1&display_description=custom\n    '
    _LOGGER = logging.getLogger(__name__)

    def get_scan_types(self):
        return ['WhiteHat Sentinel']

    def get_label_for_scan_types(self, scan_type):
        return 'WhiteHat Sentinel'

    def get_description_for_scan_types(self, scan_type):
        return 'WhiteHat Sentinel output from api/vuln/query_site can be imported in JSON format.'

    def get_findings(self, scan_file, test):
        findings_collection = json.load(scan_file)
        if (not findings_collection.keys()):
            return []
        if (('collection' not in findings_collection) or (not findings_collection['collection'])):
            msg = 'collection key not present or there were not findings present.'
            raise ValueError(msg)
        return self._convert_whitehat_sentinel_vulns_to_dojo_finding(findings_collection['collection'], test)

    def _convert_whitehat_severity_id_to_dojo_severity(self, whitehat_severity_id: int) -> typing.Union[(str, None)]:
        '\n        Converts a WhiteHat Sentinel numerical severity to a DefectDojo severity.\n\n        Args:\n            whitehat_severity_id: The WhiteHat Severity ID (called risk_id in the API)\n        Returns: A DefectDojo severity if a mapping can be found; otherwise a null value is returned\n\n        '
        severities = ['Informational', 'Informational', 'Low', 'Medium', 'High', 'Critical', 'Critical']
        try:
            return severities[int(whitehat_severity_id)]
        except IndexError:
            return None

    def _parse_cwe_from_tags(self, whitehat_sentinel_tags) -> str:
        '\n        Some Vulns include the CWE ID as a tag. This is used to pull it out of that list and return only the ID.\n\n        Args:\n            whitehat_sentinel_tags: The Tags list from the WhiteHat vuln\n        Returns: The first CWE ID in the list, if it exists\n\n        '
        for tag in whitehat_sentinel_tags:
            if tag.startswith('CWE-'):
                return tag.split('-')[1]
        return None

    def _parse_description(self, whitehat_sentinel_description: dict):
        '\n        Manually converts the HTML description to a DefectDojo-friendly format.\n\n        Args:\n            whitehat_sentinel_description: The description section of the WhiteHat Sentinel vulnerability dict\n        Returns: A dict with description and reference link\n\n        '
        description_ref = {'description': '', 'reference_link': ''}
        reference_heading_regex = '<.+>References<.+>'
        description_chunks = re.split(reference_heading_regex, whitehat_sentinel_description['description'])
        description = description_chunks[0]
        description_ref['description'] = self.__remove_paragraph_tags(description)
        if (len(description_chunks) > 1):
            description_ref['reference_link'] = self.__get_href_url(description_chunks[1])
        return description_ref

    def _parse_solution(self, whitehat_sentinel_vuln_solution):
        '\n        Manually converts the solution HTML to Markdown to avoid importing yet-another-library like Markdownify\n        Args:\n            whitehat_sentinel_vuln_solution:\n\n        '
        solution_html = whitehat_sentinel_vuln_solution['solution']
        solution_text = re.sub('<.+>', '', solution_html)
        solution_text = solution_text.split('References')[0]
        if whitehat_sentinel_vuln_solution.get('solution_prepend'):
            solution_text = f'''{solution_text}
 {whitehat_sentinel_vuln_solution.get('solution_prepend')}'''
        return solution_text

    def __get_href_url(self, text_to_search):
        '\n        Searches for the anchor targets within a string that includes an anchor tag.\n\n        Args:\n            text_to_search: The text string to search for an anchor tag\n        Returns:\n\n        '
        links = ''
        for match in re.findall('(<a href=")(https://\\S+)">', text_to_search):
            links = f'''{match[1]}
{links}'''
        return links

    def __remove_paragraph_tags(self, html_string):
        '\n        Manually remove <p> tags from HTML strings to avoid importing yet-another-library.\n\n        Args:\n            html_string: The HMTL string to remove <p> </p> tags from\n        Returns: The original string stipped of paragraph tags\n\n        '
        return re.sub('<p>|</p>', '', html_string)

    def _convert_attack_vectors_to_endpoints(self, attack_vectors: list[dict]) -> list['Endpoint']:
        '\n        Takes a list of Attack Vectors dictionaries from the WhiteHat vuln API and converts them to Defect Dojo\n        Endpoints\n        Args:\n            attack_vectors: The list of Attack Vector dictionaries\n        Returns: A list of Defect Dojo Endpoints\n        '
        return [Endpoint.from_uri(attack_vector['request']['url']) for attack_vector in attack_vectors]

    def _convert_whitehat_sentinel_vulns_to_dojo_finding(self, whitehat_sentinel_vulns: [dict], test: str):
        '\n        Converts a WhiteHat Sentinel vuln to a DefectDojo finding\n\n        Args:\n            whitehat_sentinel_vulns: The vuln dictionary from WhiteHat Sentinel vuln API\n            test: The test ID that the DefectDojo finding should be associated with\n        Returns: A DefectDojo Finding object\n\n        '
        dupes = {}
        for whitehat_vuln in whitehat_sentinel_vulns:
            date_created = whitehat_vuln['found'].split('T')[0]
            mitigated_ts = whitehat_vuln.get('closed', None)
            if (mitigated_ts is not None):
                mitigated_ts = datetime.strptime(mitigated_ts, '%Y-%m-%dT%H:%M:%SZ')
            cwe = self._parse_cwe_from_tags(whitehat_vuln['attack_vectors'][0].get('scanner_tags', []))
            description_ref = self._parse_description(whitehat_vuln['description'])
            description = description_ref['description']
            references = f'''https://source.whitehatsec.com/asset-management/site-summary/{whitehat_vuln['site']}/findings/{whitehat_vuln['id']}
{description_ref['reference_link']}'''
            steps = whitehat_vuln['description'].get('description_prepend', '')
            solution = self._parse_solution(whitehat_vuln['solution'])
            risk_id = (whitehat_vuln.get('custom_risk') or whitehat_vuln.get('risk'))
            severity = self._convert_whitehat_severity_id_to_dojo_severity(risk_id)
            false_positive = (whitehat_vuln.get('status') == 'invalid')
            active = (whitehat_vuln.get('status') in 'open')
            is_mitigated = (not active)
            dupe_key = hashlib.md5(whitehat_vuln['id'].encode('utf-8'), usedforsecurity=False).hexdigest()
            if (dupe_key in dupes):
                finding = dupes[dupe_key]
                dupes[dupe_key] = finding
            else:
                dupes[dupe_key] = True
                finding = Finding(title=whitehat_vuln['class'], test=test, cwe=cwe, active=active, verified=True, description=description, steps_to_reproduce=steps, mitigation=solution, references=references, severity=severity, false_p=false_positive, date=date_created, is_mitigated=is_mitigated, mitigated=mitigated_ts, last_reviewed=whitehat_vuln.get('lastRetested', None), dynamic_finding=True, created=date_created, unique_id_from_tool=whitehat_vuln['id'])
                endpoints = self._convert_attack_vectors_to_endpoints(whitehat_vuln['attack_vectors'])
                finding.unsaved_endpoints = endpoints
                dupes[dupe_key] = finding
        return list(dupes.values())
