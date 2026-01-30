# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import base64
import re
from datetime import datetime
from urllib.parse import urlparse
from defusedxml import ElementTree
from norm_findings.stubs.models import Endpoint, Finding
try:
    from norm_findings.stubs.django.conf.settings import QUALYS_WAS_WEAKNESS_IS_VULN
except ImportError:
    QUALYS_WAS_WEAKNESS_IS_VULN = False
try:
    from norm_findings.stubs.django.conf.settings import QUALYS_WAS_UNIQUE_ID
except ImportError:
    QUALYS_WAS_UNIQUE_ID = False
SEVERITY_MATCH = ['Low', 'Low', 'Medium', 'High', 'Critical']

def truncate_str(value: str, maxlen: int):
    if (len(value) > maxlen):
        return (value[:(maxlen - 12)] + ' (truncated)')
    return value

def get_cwe(cwe):
    cweSearch = re.search('CWE-([0-9]*)', cwe, re.IGNORECASE)
    if cweSearch:
        return cweSearch.group(1)
    return 0

def attach_unique_extras(endpoints, requests, responses, finding, date, qid, param, payload, unique_id, active_text, test):
    if (finding is None):
        finding = Finding()
        finding.unsaved_req_resp = []
        finding.unsaved_endpoints = []
        if (date is not None):
            finding.date = date
        finding.vuln_id_from_tool = str(qid)
        finding.unique_id_from_tool = unique_id
        finding.param = param
        finding.payload = payload
        finding.test = test
    elif ((date is not None) and (finding.date > date)):
        finding.date = date
    for endpoint in endpoints:
        parsedUrl = urlparse(endpoint)
        protocol = parsedUrl.scheme
        query = parsedUrl.query
        fragment = parsedUrl.fragment
        path = parsedUrl.path
        port = ''
        try:
            (host, port) = parsedUrl.netloc.split(':')
        except BaseException:
            host = parsedUrl.netloc
        finding.unsaved_endpoints.append(Endpoint(host=truncate_str(host, 500), port=port, path=truncate_str(path, 500), protocol=protocol, query=truncate_str(query, 1000), fragment=truncate_str(fragment, 500)))
    for i in range(len(requests)):
        if (requests[i] or responses[i]):
            finding.unsaved_req_resp.append({'req': requests[i], 'resp': responses[i]})
    if (active_text is not None):
        if ('fixed' in active_text.lower()):
            finding.active = False
        else:
            finding.active = True
    return finding

def attach_extras(endpoints, requests, responses, finding, date, qid, test):
    if (finding is None):
        finding = Finding()
        finding.unsaved_req_resp = []
        finding.unsaved_endpoints = []
        finding.test = test
        if (date is not None):
            finding.date = date
        finding.vuln_id_from_tool = str(qid)
    elif ((date is not None) and (finding.date > date)):
        finding.date = date
    for endpoint in endpoints:
        finding.unsaved_endpoints.append(Endpoint.from_uri(endpoint))
    for i in range(len(requests)):
        if (requests[i] or responses[i]):
            finding.unsaved_req_resp.append({'req': requests[i], 'resp': responses[i]})
    return finding

def get_request(request):
    if (request is not None):
        header = ''
        header += (str(request.findtext('METHOD')) + ': ')
        header += (str(request.findtext('URL')) + '\n')
        headers = request.find('HEADERS')
        if (headers is not None):
            for head in headers.iter('HEADER'):
                header += (str(head.findtext('key')) + ': ')
                header += (str(head.findtext('value')) + '\n')
        if (request.findtext('BODY') is not None):
            header += (('BODY: ' + str(request.findtext('BODY'))) + '\n')
        return str(header)
    return ''

def get_response(response):
    if (response is not None):
        return decode_tag(response.find('CONTENTS'))
    return ''

def decode_tag(tag):
    if (tag is not None):
        if (tag.get('base64') == 'true'):
            return base64.b64decode(tag.text).decode('utf8', 'replace')
        return tag.text
    return ''

def get_request_response(payloads):
    requests = []
    responses = []
    for payload in payloads.iter('PAYLOAD'):
        requests.append(get_request(payload.find('REQUEST')))
        responses.append(get_response(payload.find('RESPONSE')))
    return [requests, responses]

def get_unique_vulnerabilities(vulnerabilities, test, *, is_info=False, is_app_report=False):
    findings = {}
    for vuln in vulnerabilities:
        urls = []
        qid = int(vuln.findtext('QID'))
        url = vuln.findtext('URL')
        if (url is not None):
            urls.append(str(url))
        access_path = vuln.find('ACCESS_PATH')
        if (access_path is not None):
            urls += [url.text for url in access_path.iter('URL')]
        payloads = vuln.find('PAYLOADS')
        req_resps = (get_request_response(payloads) if (payloads is not None) else [[], []])
        if is_info:
            raw_finding_date = vuln.findtext('LAST_TIME_DETECTED')
        elif is_app_report:
            raw_finding_date = vuln.findtext('FIRST_TIME_DETECTED')
        else:
            raw_finding_date = vuln.findtext('DETECTION_DATE')
        if (raw_finding_date is not None):
            if raw_finding_date.endswith('GMT'):
                finding_date = datetime.strptime(raw_finding_date, '%d %b %Y %I:%M%p GMT')
            else:
                finding_date = datetime.strptime(raw_finding_date, '%d %b %Y %I:%M%p GMT%z')
        else:
            finding_date = None
        unique_id = vuln.findtext('UNIQUE_ID')
        active_text = vuln.findtext('STATUS')
        param = None
        payload = None
        if (not is_info):
            param = vuln.findtext('PARAM')
            payload = vuln.findtext('PAYLOADS/PAYLOAD/PAYLOAD')
        findings[unique_id] = attach_unique_extras(urls, req_resps[0], req_resps[1], None, finding_date, qid, param, payload, unique_id, active_text, test)
    return findings

def get_vulnerabilities(vulnerabilities, test, *, is_info=False, is_app_report=False):
    findings = {}
    for vuln in vulnerabilities:
        urls = []
        qid = int(vuln.findtext('QID'))
        url = vuln.findtext('URL')
        if (url is not None):
            urls.append(str(url))
        access_path = vuln.find('ACCESS_PATH')
        if (access_path is not None):
            urls += [url.text for url in access_path.iter('URL')]
        payloads = vuln.find('PAYLOADS')
        req_resps = (get_request_response(payloads) if (payloads is not None) else [[], []])
        if is_info:
            raw_finding_date = vuln.findtext('LAST_TIME_DETECTED')
        elif is_app_report:
            raw_finding_date = vuln.findtext('FIRST_TIME_DETECTED')
        else:
            raw_finding_date = vuln.findtext('DETECTION_DATE')
        if (raw_finding_date is not None):
            if raw_finding_date.endswith('GMT'):
                finding_date = datetime.strptime(raw_finding_date, '%d %b %Y %I:%M%p GMT')
            else:
                finding_date = datetime.strptime(raw_finding_date, '%d %b %Y %I:%M%p GMT%z')
        else:
            finding_date = None
        finding = findings.get(qid)
        findings[qid] = attach_extras(urls, req_resps[0], req_resps[1], finding, finding_date, qid, test)
    return findings

def get_glossary_item(glossary, finding, *, is_info=False, enable_weakness=False):
    title = glossary.findtext('TITLE')
    if (title is not None):
        finding.title = str(title)
    severity = glossary.findtext('SEVERITY')
    if (severity is not None):
        group = glossary.findtext('GROUP')
        if (is_info and ((not enable_weakness) or (group in {'DIAG', 'IG'}))):
            finding.severity = 'Info'
        else:
            finding.severity = SEVERITY_MATCH[(int(severity) - 1)]
    description = glossary.findtext('DESCRIPTION')
    if (description is not None):
        finding.description = str(description)
    impact = glossary.findtext('IMPACT')
    if (impact is not None):
        finding.impact = str(impact)
    solution = glossary.findtext('SOLUTION')
    if (solution is not None):
        finding.mitigation = str(solution)
    cwe = glossary.findtext('CWE')
    if (cwe is not None):
        finding.cwe = int(get_cwe(str(cwe)))
    return finding

def get_info_item(info_gathered, finding):
    data = info_gathered.find('DATA')
    if (data is not None):
        finding.description += ('\n\n' + decode_tag(data))
    return finding

def get_unique_items(vulnerabilities, info_gathered, glossary, is_app_report, test, *, enable_weakness=False):
    ig_qid_list = [int(ig.findtext('QID')) for ig in info_gathered]
    g_qid_list = [int(g.findtext('QID')) for g in glossary]
    findings = {}
    for (unique_id, finding) in get_unique_vulnerabilities(vulnerabilities, test, is_info=False, is_app_report=is_app_report).items():
        qid = int(finding.vuln_id_from_tool)
        if (qid in g_qid_list):
            index = g_qid_list.index(qid)
            findings[unique_id] = get_glossary_item(glossary[index], finding, is_info=False, enable_weakness=enable_weakness)
    for (unique_id, finding) in get_unique_vulnerabilities(info_gathered, test, is_info=True, is_app_report=is_app_report).items():
        qid = int(finding.vuln_id_from_tool)
        if (qid in g_qid_list):
            index = g_qid_list.index(qid)
            final_finding = get_glossary_item(glossary[index], finding, is_info=True, enable_weakness=enable_weakness)
        else:
            final_finding = finding
        if (qid in ig_qid_list):
            index = ig_qid_list.index(qid)
            findings[unique_id] = get_info_item(info_gathered[index], final_finding)
    return findings

def get_items(vulnerabilities, info_gathered, glossary, is_app_report, test, *, enable_weakness=False):
    ig_qid_list = [int(ig.findtext('QID')) for ig in info_gathered]
    g_qid_list = [int(g.findtext('QID')) for g in glossary]
    findings = {}
    for (qid, finding) in get_vulnerabilities(vulnerabilities, test, is_info=False, is_app_report=is_app_report).items():
        if (qid in g_qid_list):
            index = g_qid_list.index(qid)
            findings[qid] = get_glossary_item(glossary[index], finding, is_info=False, enable_weakness=enable_weakness)
    for (qid, finding) in get_vulnerabilities(info_gathered, test, is_info=True, is_app_report=is_app_report).items():
        if (qid in g_qid_list):
            index = g_qid_list.index(qid)
            final_finding = get_glossary_item(glossary[index], finding, is_info=True, enable_weakness=enable_weakness)
        else:
            final_finding = finding
        if (qid in ig_qid_list):
            index = ig_qid_list.index(qid)
            findings[qid] = get_info_item(info_gathered[index], final_finding)
    return findings

def qualys_webapp_parser(qualys_xml_file, test, unique, *, enable_weakness=False):
    if (qualys_xml_file is None):
        return []
    tree = ElementTree.parse(qualys_xml_file)
    is_app_report = (tree.getroot().tag == 'WAS_WEBAPP_REPORT')
    if is_app_report:
        vulnerabilities = tree.findall('./RESULTS/WEB_APPLICATION/VULNERABILITY_LIST/VULNERABILITY')
        info_gathered = tree.findall('./RESULTS/WEB_APPLICATION/INFORMATION_GATHERED_LIST/INFORMATION_GATHERED')
    else:
        vulnerabilities = tree.findall('./RESULTS/VULNERABILITY_LIST/VULNERABILITY')
        info_gathered = tree.findall('./RESULTS/INFORMATION_GATHERED_LIST/INFORMATION_GATHERED')
    glossary = tree.findall('./GLOSSARY/QID_LIST/QID')
    if unique:
        items = list(get_unique_items(vulnerabilities, info_gathered, glossary, is_app_report, test, enable_weakness=enable_weakness).values())
    else:
        items = list(get_items(vulnerabilities, info_gathered, glossary, is_app_report, test, enable_weakness=enable_weakness).values())
    return list(items)

class QualysWebAppParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Qualys Webapp Parser.\n\n        Fields:\n        - date: Set to date from Qualys Webapp Scanner.\n        - vuln_id_from_tool: Set to qid from Qualys Webapp Scanner.\n        - unique_id_from_tool: Set to the unique id from Qualys Webapp Scanner.\n        - param: Set to param from Qualys Webapp Scanner.\n        - payload: Set to payload from Qualys Webapp Scanner.\n        - active: Set to true or false based on finding status.\n        - title: Set to title from Qualys Webapp Scanner.\n        - severity: Set to severity from Qualys Webapp Scanner translated into DefectDojo formant.\n        - description: Custom description made from description and data from Qualys Webapp Scanner.\n        - impact: Set to title from Qualys Webapp Scanner.\n        - mitigation: Set to solution from Qualys Webapp Scanner.\n        - cwe: Set to cwe from Qualys Webapp Scanner.\n        '
        return ['date', 'vuln_id_from_tool', 'unique_id_from_tool', 'param', 'payload', 'active', 'title', 'severity', 'impact', 'mitigation', 'cwe']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Qualys Webapp Parser.\n\n        Fields:\n        - title: Set to title from Qualys Webapp Scanner.\n        - unique_id_from_tool: Set to the unique id from Qualys Webapp Scanner.\n        '
        return ['title', 'unique_id_from_tool']

    def get_scan_types(self):
        return ['Qualys Webapp Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Qualys WebScan output files can be imported in XML format.'

    def get_findings(self, scan_file, test, enable_weakness=QUALYS_WAS_WEAKNESS_IS_VULN):
        return qualys_webapp_parser(scan_file, test, QUALYS_WAS_UNIQUE_ID, enable_weakness=enable_weakness)
