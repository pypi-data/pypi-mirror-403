# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import re
import uuid
from datetime import datetime
from defusedxml import ElementTree
from norm_findings.stubs.django.conf import settings
from norm_findings.stubs.models import Endpoint, Finding
XML_NAMESPACE = {'x': 'https://www.veracode.com/schema/reports/export/1.0'}

class VeracodeXMLParser():
    '\n    This parser is written for Veracode Detailed XML reports, version 1.5.\n\n    Version is annotated in the report, `detailedreport/@report_format_version`.\n    see https://help.veracode.com/r/t_download_XML_report\n    '
    vc_severity_mapping = {1: 'Info', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}

    def get_findings(self, scan_file, test):
        root = ElementTree.parse(scan_file).getroot()
        app_id = root.attrib['app_id']
        report_date = datetime.strptime(root.attrib['last_update_time'], '%Y-%m-%d %H:%M:%S %Z')
        dupes = {}
        for category_node in root.findall('x:severity/x:category', namespaces=XML_NAMESPACE):
            mitigation_text = ''
            mitigation_text += (category_node.find('x:recommendations/x:para', namespaces=XML_NAMESPACE).get('text') + '\n\n')
            mitigation_text += ''.join([(('    * ' + x.get('text')) + '\n') for x in category_node.findall('x:recommendations/x:para/x:bulletitem', namespaces=XML_NAMESPACE)])
            for flaw_node in category_node.findall('x:cwe/x:staticflaws/x:flaw', namespaces=XML_NAMESPACE):
                dupe_key = flaw_node.attrib['issueid']
                if (dupe_key not in dupes):
                    dupes[dupe_key] = self.__xml_static_flaw_to_finding(app_id, flaw_node, mitigation_text, test)
            for flaw_node in category_node.findall('x:cwe/x:dynamicflaws/x:flaw', namespaces=XML_NAMESPACE):
                dupe_key = flaw_node.attrib['issueid']
                if (dupe_key not in dupes):
                    dupes[dupe_key] = self.__xml_dynamic_flaw_to_finding(app_id, flaw_node, mitigation_text, test)
        for component in root.findall('x:software_composition_analysis/x:vulnerable_components/x:component', namespaces=XML_NAMESPACE):
            library = component.attrib['library']
            if (('library_id' in component.attrib) and component.attrib['library_id'].startswith('maven:')):
                split_library_id = component.attrib['library_id'].split(':')
                if (len(split_library_id) > 2):
                    library = split_library_id[2]
            vendor = component.attrib['vendor']
            version = component.attrib['version']
            for vulnerability in component.findall('x:vulnerabilities/x:vulnerability', namespaces=XML_NAMESPACE):
                dupes[str(uuid.uuid4())] = self.__xml_sca_flaw_to_finding(test, report_date, vendor, library, version, vulnerability)
        return list(dupes.values())

    @classmethod
    def __xml_flaw_to_unique_id(cls, app_id, xml_node):
        issue_id = xml_node.attrib['issueid']
        return ((('app-' + app_id) + '_issue-') + issue_id)

    @classmethod
    def __xml_flaw_to_severity(cls, xml_node):
        return cls.vc_severity_mapping.get(int(xml_node.attrib['severity']), 'Info')

    @classmethod
    def __xml_flaw_to_finding(cls, app_id, xml_node, mitigation_text, test):
        finding = Finding()
        finding.test = test
        finding.mitigation = mitigation_text
        finding.static_finding = True
        finding.dynamic_finding = False
        finding.unique_id_from_tool = cls.__xml_flaw_to_unique_id(app_id, xml_node)
        finding.severity = cls.__xml_flaw_to_severity(xml_node)
        finding.cwe = int(xml_node.attrib['cweid'])
        finding.title = xml_node.attrib['categoryname']
        finding.impact = ('CIA Impact: ' + xml_node.attrib['cia_impact'].upper())
        description = xml_node.attrib['description'].replace('. ', '.\n')
        finding.description = description
        references = 'None'
        if ('References:' in description):
            references = description[(description.index('References:') + 13):].replace(')  ', ')\n')
        finding.references = ((((((references + '\n\nVulnerable Module: ') + xml_node.attrib['module']) + '\nType: ') + xml_node.attrib['type']) + '\nVeracode issue ID: ') + xml_node.attrib['issueid'])
        try:
            if settings.USE_FIRST_SEEN:
                if (date := xml_node.get('date_first_occurrence', None)):
                    finding.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S %Z')
            elif (date := xml_node.get('date_last_occurrence', None)):
                finding.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S %Z')
        except Exception:
            finding.date = test.target_start
        is_mitigated = False
        mitigated_date = None
        if (('mitigation_status' in xml_node.attrib) and (xml_node.attrib['mitigation_status'].lower() == 'accepted')):
            if (('remediation_status' in xml_node.attrib) and (xml_node.attrib['remediation_status'].lower() == 'fixed')):
                is_mitigated = True
            else:
                for mitigation in xml_node.findall('x:mitigations/x:mitigation', namespaces=XML_NAMESPACE):
                    is_mitigated = True
                    mitigated_date = datetime.strptime(mitigation.attrib['date'], '%Y-%m-%d %H:%M:%S %Z')
        finding.is_mitigated = is_mitigated
        finding.mitigated = mitigated_date
        finding.active = (not is_mitigated)
        false_positive = False
        if is_mitigated:
            remediation_status = xml_node.attrib['remediation_status'].lower()
            if (('false positive' in remediation_status) or ('falsepositive' in remediation_status)):
                false_positive = True
        finding.false_p = false_positive
        return finding

    @classmethod
    def __xml_static_flaw_to_finding(cls, app_id, xml_node, mitigation_text, test):
        finding = cls.__xml_flaw_to_finding(app_id, xml_node, mitigation_text, test)
        finding.static_finding = True
        finding.dynamic_finding = False
        line_number = xml_node.attrib['line']
        functionrelativelocation = xml_node.attrib['functionrelativelocation']
        if ((line_number is not None) and line_number.isdigit() and (functionrelativelocation is not None) and functionrelativelocation.isdigit()):
            finding.line = (int(line_number) + int(functionrelativelocation))
            finding.sast_source_line = finding.line
        source_file = xml_node.attrib.get('sourcefile')
        sourcefilepath = xml_node.attrib.get('sourcefilepath')
        finding.file_path = (sourcefilepath + source_file)
        finding.sast_source_file_path = (sourcefilepath + source_file)
        sast_source_obj = xml_node.attrib.get('functionprototype')
        if isinstance(sast_source_obj, str):
            finding.sast_source_object = (sast_source_obj or None)
        finding.unsaved_tags = ['sast']
        return finding

    @classmethod
    def __xml_dynamic_flaw_to_finding(cls, app_id, xml_node, mitigation_text, test):
        finding = cls.__xml_flaw_to_finding(app_id, xml_node, mitigation_text, test)
        finding.static_finding = False
        finding.dynamic_finding = True
        url_host = xml_node.attrib.get('url')
        finding.unsaved_endpoints = [Endpoint.from_uri(url_host)]
        finding.unsaved_tags = ['dast']
        return finding

    @staticmethod
    def _get_cwe(val):
        cweSearch = re.search('CWE-(\\d+)', val, re.IGNORECASE)
        if cweSearch:
            return int(cweSearch.group(1))
        return None

    @classmethod
    def __xml_sca_flaw_to_finding(cls, test, report_date, _vendor, library, version, xml_node):
        finding = Finding()
        finding.test = test
        finding.static_finding = True
        finding.dynamic_finding = False
        cvss_score = float(xml_node.attrib['cvss_score'])
        finding.cvssv3_score = cvss_score
        finding.severity = cls.__xml_flaw_to_severity(xml_node)
        finding.unsaved_vulnerability_ids = [xml_node.attrib['cve_id']]
        finding.cwe = cls._get_cwe(xml_node.attrib['cwe_id'])
        finding.title = f'Vulnerable component: {library}:{version}'
        finding.component_name = library
        finding.component_version = version
        finding.date = report_date
        description = 'This library has known vulnerabilities.\n'
        description += '**CVE:** {} ({})\nCVS Score: {} ({})\nSummary: \n>{}\n\n-----\n\n'.format(xml_node.attrib['cve_id'], xml_node.attrib.get('first_found_date'), xml_node.attrib['cvss_score'], cls.vc_severity_mapping.get(int(xml_node.attrib['severity']), 'Info'), xml_node.attrib['cve_summary'])
        finding.description = description
        finding.unsaved_tags = ['sca']
        is_mitigated = False
        mitigated_date = None
        if (('mitigation' in xml_node.attrib) and (xml_node.attrib['mitigation'].lower() == 'true')):
            for mitigation in xml_node.findall('x:mitigations/x:mitigation', namespaces=XML_NAMESPACE):
                is_mitigated = True
                mitigated_date = datetime.strptime(mitigation.attrib['date'], '%Y-%m-%d %H:%M:%S %Z')
        finding.is_mitigated = is_mitigated
        finding.mitigated = mitigated_date
        finding.active = (not is_mitigated)
        return finding
