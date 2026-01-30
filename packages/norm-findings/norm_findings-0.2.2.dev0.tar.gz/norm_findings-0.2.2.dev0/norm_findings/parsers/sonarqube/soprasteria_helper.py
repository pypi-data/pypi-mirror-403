# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import logging
import re
from norm_findings.stubs.django.utils.html import strip_tags
from lxml import etree
from norm_findings.stubs.models import Finding
logger = logging.getLogger(__name__)

class SonarQubeSoprasteriaHelper():

    def convert_sonar_severity(self, sonar_severity):
        sev = sonar_severity.lower()
        if (sev == 'blocker'):
            return 'Critical'
        if (sev == 'critical'):
            return 'High'
        if (sev == 'major'):
            return 'Medium'
        if (sev == 'minor'):
            return 'Low'
        if (sev in {'high', 'medium', 'low'}):
            return sev.capitalize()
        return 'Info'

    def get_description(self, vuln_details):
        rule_description = etree.tostring(vuln_details, pretty_print=True).decode('utf-8', errors='replace')
        rule_description = rule_description.split('<h2>See', 1)[0]
        rule_description = str(rule_description).replace('<h2>', '**')
        rule_description = str(rule_description).replace('</h2>', '**')
        return strip_tags(rule_description).strip()

    def get_references(self, rule_name, vuln_details):
        rule_references = rule_name
        for a in vuln_details.iter('a'):
            rule_references += ('\n' + str(a.text))
        return rule_references

    def get_cwe(self, vuln_references):
        cweSearch = re.search('CWE-([0-9]*)', vuln_references, re.IGNORECASE)
        if cweSearch:
            return cweSearch.group(1)
        return 0

    def process_result_file_name_aggregated(self, test, dupes, vuln_title, vuln_cwe, vuln_description, vuln_file_path, vuln_line, vuln_severity, vuln_mitigation, vuln_references):
        aggregateKeys = f'{vuln_cwe}{vuln_title}{vuln_description}{vuln_file_path}'
        descriptionOneOccurence = f'Line: {vuln_line}'
        if (aggregateKeys not in dupes):
            find = Finding(title=vuln_title, cwe=int(vuln_cwe), description=((vuln_description + '\n\n-----\nOccurences:\n') + descriptionOneOccurence), file_path=vuln_file_path, test=test, severity=vuln_severity, mitigation=vuln_mitigation, references=vuln_references, false_p=False, duplicate=False, out_of_scope=False, mitigated=None, impact='No impact provided', static_finding=True, dynamic_finding=False, nb_occurences=1)
            dupes[aggregateKeys] = find
        else:
            find = dupes[aggregateKeys]
            find.description = f'''{find.description}
{descriptionOneOccurence}'''
            find.mitigation = f'''{find.mitigation}
______
{vuln_mitigation}'''
            find.nb_occurences += 1

    def process_result_detailed(self, test, dupes, vuln_title, vuln_cwe, vuln_description, vuln_file_path, vuln_line, vuln_severity, vuln_mitigation, vuln_references, vuln_key):
        aggregateKeys = f'{vuln_cwe}{vuln_title}{vuln_description}{vuln_file_path}{vuln_key}'
        find = Finding(title=vuln_title, cwe=int(vuln_cwe), description=vuln_description, file_path=vuln_file_path, line=vuln_line, test=test, severity=vuln_severity, mitigation=vuln_mitigation, references=vuln_references, false_p=False, duplicate=False, out_of_scope=False, mitigated=None, impact='No impact provided', static_finding=True, dynamic_finding=False, unique_id_from_tool=vuln_key)
        dupes[aggregateKeys] = find
