# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import datetime
import logging
import html2text
from cvss import CVSS3
from defusedxml import ElementTree
from norm_findings.stubs.django.conf import settings
from norm_findings.stubs.models import Endpoint, Finding
from norm_findings.parsers.qualys import csv_parser
from norm_findings.stubs.utils import parse_cvss_data
logger = logging.getLogger(__name__)

class QualysParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Qualys Parser.\n\n        Fields:\n        - title: Set to gid and vulnerability name from Qualys Scanner\n        - mitigation: Set to solution from Qualys Scanner\n        - description: Custom description made from: description, category, QID, port, result evidence, first found, last found, and times found.\n        - severity: Set to severity from Qualys Scanner translated into DefectDojo formant.\n        - impact: Set to impact from Qualys Scanner.\n        - date: Set to datetime from Qualys Scanner.\n        - vuln_id_from_tool: Set to gid from Qualys Scanner.\n        - mitigated: Set to the mitigation_date from Qualys Scanner\n        - is_mitigated: Set to true or false based on pressence of "mitigated" in Qualys Scanner output.\n        - active: Set to true if status equals active, re-opened, or new; else set to false.\n        - cvssv3: Set to CVSS_vector if not null.\n        - verified: Set to true.\n\n        Return the list of fields used in the Qualys CSV Parser.\n\n        Fields:\n        - title: Set to gid and vulnerability name from Qualys Scanner\n        - mitigation: Set to solution from Qualys Scanner\n        - description: Custom description made from: description, category, QID, port, result evidence, first found, last found, and times found.\n        - severity: Set to severity from Qualys Scanner translated into DefectDojo formant.\n        - impact: Set to impact from Qualys Scanner.\n        - date: Set to datetime from Qualys Scanner.\n        - vuln_id_from_tool: Set to gid from Qualys Scanner.\n        - mitigated: Set to the mitigation_date from Qualys Scanner\n        - is_mitigated: Set to true or false based on pressence of "mitigated" in Qualys Scanner output.\n        - active: Set to true if status equals active, re-opened, or new; else set to false.\n        - cvssv3: Set to CVSS_vector if not null.\n        - verified: Set to true.\n        '
        return ['title', 'mitigation', 'description', 'severity', 'impact', 'date', 'vuln_id_from_tool', 'mitigated', 'is_mitigated', 'active', 'cvssv3', 'verified']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Qualys and Qualys CSV Parser.\n\n        Fields:\n        - title: Set to gid and vulnerability name from Qualys Scanner\n        - severity: Set to severity from Qualys Scanner translated into DefectDojo formant.\n\n        #NOTE: endpoints is not provided by parser\n        '
        return ['title', 'severity']

    def get_scan_types(self):
        return ['Qualys Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Qualys Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Qualys WebGUI output files can be imported in XML format.'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith('.csv'):
            return csv_parser.parse_csv(scan_file)
        return qualys_parser(scan_file)
CUSTOM_HEADERS = {'CVSS_score': 'CVSS Score', 'ip_address': 'IP Address', 'fqdn': 'FQDN', 'os': 'OS', 'port_status': 'Port', 'vuln_name': 'Vulnerability', 'vuln_description': 'Description', 'solution': 'Solution', 'links': 'Links', 'cve': 'CVE', 'vuln_severity': 'Severity', 'QID': 'QID', 'first_found': 'First Found', 'last_found': 'Last Found', 'found_times': 'Found Times', 'category': 'Category'}
REPORT_HEADERS = ['CVSS_score', 'ip_address', 'fqdn', 'os', 'port_status', 'vuln_name', 'vuln_description', 'solution', 'links', 'cve', 'Severity', 'QID', 'first_found', 'last_found', 'found_times', 'category']
TYPE_MAP = {'Ig': 'INFORMATION GATHERED', 'Practice': 'POTENTIAL', 'Vuln': 'CONFIRMED'}
LEGACY_SEVERITY_LOOKUP = {1: 'Informational', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}
NON_LEGACY_SEVERITY_LOOKUP = {'Informational': 'Low', 'Low': 'Low', 'Medium': 'Medium', 'High': 'High', 'Critical': 'High'}

def get_severity(severity_value_str: typing.Union[(str, None)]) -> str:
    severity_value: int = int((severity_value_str or (- 1)))
    sev: str = LEGACY_SEVERITY_LOOKUP.get(severity_value, 'Unknown')
    if (not settings.USE_QUALYS_LEGACY_SEVERITY_PARSING):
        sev: str = NON_LEGACY_SEVERITY_LOOKUP.get(sev, 'Unknown')
    if (sev == 'Unknown'):
        logger.warning('Could not determine severity from severity_value_str: %s', severity_value_str)
        sev = 'Informational'
    return sev

def htmltext(blob):
    h = html2text.HTML2Text()
    h.ignore_links = False
    return h.handle(blob)

def split_cvss(value, _temp):
    if ((value is None) or (len(value) == 0) or (value == '-')):
        return
    if (len(value) > 4):
        split = value.split(' (')
        if (_temp.get('CVSS_value') is None):
            _temp['CVSS_value'] = float(split[0])
        if (_temp.get('CVSS_vector') is None):
            _temp['CVSS_vector'] = CVSS3(('CVSS:3.0/' + split[1][:(- 1)])).clean_vector()
    elif (_temp.get('CVSS_value') is None):
        _temp['CVSS_value'] = float(value)

def parse_finding(host, tree):
    ret_rows = []
    issue_row = {}
    issue_row['ip_address'] = host.findtext('IP')
    issue_row['fqdn'] = host.findtext('DNS')
    ep = (Endpoint(host=issue_row['fqdn']) if issue_row['fqdn'] else Endpoint(host=issue_row['ip_address']))
    issue_row['os'] = host.findtext('OPERATING_SYSTEM')
    for vuln_details in host.iterfind('VULN_INFO_LIST/VULN_INFO'):
        temp = issue_row.copy()
        gid = vuln_details.find('QID').attrib['id']
        port = vuln_details.findtext('PORT')
        temp['port_status'] = port
        category = str(vuln_details.findtext('CATEGORY'))
        result = str(vuln_details.findtext('RESULT'))
        first_found = str(vuln_details.findtext('FIRST_FOUND'))
        last_found = str(vuln_details.findtext('LAST_FOUND'))
        times_found = str(vuln_details.findtext('TIMES_FOUND'))
        try:
            if settings.USE_FIRST_SEEN:
                if (date := vuln_details.findtext('FIRST_FOUND')):
                    temp['date'] = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').date()
            elif (date := vuln_details.findtext('LAST_FOUND')):
                temp['date'] = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').date()
        except Exception:
            temp['date'] = None
        status = vuln_details.findtext('VULN_STATUS')
        if (status in {'Active', 'Re-Opened', 'New'}):
            temp['active'] = True
            temp['mitigated'] = False
            temp['mitigation_date'] = None
        else:
            temp['active'] = False
            temp['mitigated'] = True
            last_fixed = vuln_details.findtext('LAST_FIXED')
            if (last_fixed is not None):
                temp['mitigation_date'] = datetime.datetime.strptime(last_fixed, '%Y-%m-%dT%H:%M:%SZ')
            else:
                temp['mitigation_date'] = None
        cvss3 = vuln_details.findtext('CVSS3_FINAL')
        if ((cvss3 is not None) and (cvss3 != '-')):
            split_cvss(cvss3, temp)
        else:
            cvss2 = vuln_details.findtext('CVSS_FINAL')
            if ((cvss2 is not None) and (cvss2 != '-')):
                split_cvss(cvss2, temp)
                temp['CVSS_vector'] = None
        search = f".//GLOSSARY/VULN_DETAILS_LIST/VULN_DETAILS[@id='{gid}']"
        vuln_item = tree.find(search)
        if (vuln_item is not None):
            finding = Finding()
            temp['vuln_name'] = vuln_item.findtext('TITLE')
            description = str(vuln_item.findtext('THREAT'))
            temp['solution'] = htmltext(vuln_item.findtext('SOLUTION'))
            vul_type = TYPE_MAP.get(vuln_details.findtext('TYPE'), 'Unknown')
            temp['vuln_description'] = '\n'.join([htmltext(description), htmltext(('Type: ' + vul_type)), htmltext(('Category: ' + category)), htmltext(('QID: ' + str(gid))), htmltext(('Port: ' + str(port))), htmltext(('Result Evidence: ' + result)), htmltext(('First Found: ' + first_found)), htmltext(('Last Found: ' + last_found)), htmltext(('Times Found: ' + times_found))])
            temp['IMPACT'] = htmltext(vuln_item.findtext('IMPACT'))
            if (temp.get('CVSS_value') is None):
                cvss3 = vuln_item.findtext('CVSS3_SCORE/CVSS3_BASE')
                cvss2 = vuln_item.findtext('CVSS_SCORE/CVSS_BASE')
                if ((cvss3 is not None) and (cvss3 != '-')):
                    split_cvss(cvss3, temp)
                else:
                    cvss2 = vuln_item.findtext('CVSS_FINAL')
                    if ((cvss2 is not None) and (cvss2 != '-')):
                        split_cvss(cvss2, temp)
                        temp['CVSS_vector'] = None
            temp_cve_details = [(cve.findtext('ID'), cve.findtext('URL')) for cve in vuln_item.iterfind('CVE_ID_LIST/CVE_ID')]
            temp['cve_list'] = [cve_id for (cve_id, _) in temp_cve_details if cve_id]
            temp['links'] = [url for (_, url) in temp_cve_details if url]
        sev = get_severity(vuln_item.findtext('SEVERITY'))
        finding = None
        if temp_cve_details:
            refs = temp.get('links', '')
            finding = Finding(title=((('QID-' + gid[4:]) + ' | ') + temp['vuln_name']), mitigation=temp['solution'], description=temp['vuln_description'], severity=sev, references=refs, impact=temp['IMPACT'], date=temp['date'], vuln_id_from_tool=gid)
        else:
            finding = Finding(title=((('QID-' + gid[4:]) + ' | ') + temp['vuln_name']), mitigation=temp['solution'], description=temp['vuln_description'], severity=sev, references=gid, impact=temp['IMPACT'], date=temp['date'], vuln_id_from_tool=gid)
        finding.mitigated = temp['mitigation_date']
        finding.is_mitigated = temp['mitigated']
        finding.active = temp['active']
        if (temp.get('CVSS_vector') is not None):
            cvss_data = parse_cvss_data(temp.get('CVSS_vector'))
            if cvss_data:
                finding.cvssv3 = cvss_data.get('cvssv3')
                finding.cvssv3_score = cvss_data.get('cvssv3_score')
        if (temp.get('CVSS_value') is not None):
            finding.cvssv3_score = temp.get('CVSS_value')
        finding.verified = True
        finding.unsaved_endpoints = []
        finding.unsaved_endpoints.append(ep)
        finding.unsaved_vulnerability_ids = temp.get('cve_list', [])
        ret_rows.append(finding)
    return ret_rows

def qualys_parser(qualys_xml_file):
    parser = ElementTree.XMLParser()
    tree = ElementTree.parse(qualys_xml_file, parser)
    host_list = tree.find('HOST_LIST')
    finding_list = []
    if (host_list is not None):
        for host in host_list:
            finding_list += parse_finding(host, tree)
    return finding_list
