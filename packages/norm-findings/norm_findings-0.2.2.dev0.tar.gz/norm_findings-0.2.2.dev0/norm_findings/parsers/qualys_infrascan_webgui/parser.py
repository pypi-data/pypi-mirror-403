# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import logging
from datetime import datetime
import html2text
from dateutil import parser
from defusedxml import ElementTree
from norm_findings.stubs.models import Endpoint, Finding
logger = logging.getLogger(__name__)

def htmltext(blob):
    h = html2text.HTML2Text()
    h.ignore_links = False
    return h.handle(blob)

def issue_r(raw_row, vuln, scan_date):
    ret_rows = []
    issue_row = {}
    issue_row['ip_address'] = raw_row.get('value')
    issue_row['fqdn'] = raw_row.get('name')
    if (issue_row['fqdn'] == 'No registered hostname'):
        issue_row['fqdn'] = None
    port = raw_row.get('port')
    ep = (Endpoint(host=issue_row['fqdn']) if issue_row['fqdn'] else Endpoint(host=issue_row['ip_address']))
    issue_row['os'] = raw_row.findtext('OS')
    for vuln_cat in raw_row.findall('VULNS/CAT'):
        category = str(vuln_cat.get('value'))
        for vuln_details in vuln_cat.findall('VULN'):
            temp = issue_row
            gid = vuln_details.get('number')
            temp['port_status'] = port
            result = str(vuln_details.findtext('RESULT'))
            temp['vuln_name'] = vuln_details.findtext('TITLE')
            description = str(vuln_details.findtext('DIAGNOSIS'))
            temp['solution'] = htmltext(str(vuln_details.findtext('SOLUTION')))
            temp['vuln_description'] = '\n'.join([htmltext(description), htmltext(('**Category:** ' + category)), htmltext(('**QID:** ' + str(gid))), htmltext(('**Port:** ' + str(port))), htmltext(('**Result Evidence:** ' + result))])
            temp['IMPACT'] = htmltext(str(vuln_details.findtext('CONSEQUENCE')))
            cl = []
            temp_cve_details = vuln_details.iterfind('CVE_ID_LIST/CVE_ID')
            if temp_cve_details:
                cl = {cve_detail.findtext('ID'): cve_detail.findtext('URL') for cve_detail in temp_cve_details}
                temp['cve'] = '\n'.join(list(cl.keys()))
                temp['links'] = '\n'.join(list(cl.values()))
            sev = qualys_convert_severity(vuln_details.get('severity'))
            refs = '\n'.join(list(cl.values()))
            finding = Finding(title=temp['vuln_name'], mitigation=temp['solution'], description=temp['vuln_description'], severity=sev, references=refs, impact=temp['IMPACT'], vuln_id_from_tool=gid, date=scan_date)
            finding.unsaved_endpoints = []
            finding.unsaved_endpoints.append(ep)
            ret_rows.append(finding)
    return ret_rows

def qualys_convert_severity(raw_val):
    val = str(raw_val).strip()
    if (val == '1'):
        return 'Info'
    if (val == '2'):
        return 'Low'
    if (val == '3'):
        return 'Medium'
    if (val == '4'):
        return 'High'
    if (val == '5'):
        return 'Critical'
    return 'Info'

class QualysInfrascanWebguiParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Qualys Infrastructure Webgui Parser.\n\n        Fields:\n        - title: Set to title from Qualys Infrastructure Webgui Scanner.\n        - mitigation: Set to solution from Qualys Infrastructure Webgui Scanner.\n        - description: Custom description made from: description, category, QID, port, and result evidence.\n        - severity: Set to severity from Qualys Infrastructure Webgui Scanner translated into DefectDojo formant.\n        - impact: Set to consequence from Qualys Infrastructure Webgui Scanner.\n        - vuln_id_from_tool: Set to gid from Qualys Infrastructure Webgui Scanner.\n        - date: Set to datetime from Qualys Infrastructure Webgui Scanner.\n        '
        return ['title', 'mitigation', 'description', 'severity', 'impact', 'vuln_id_from_tool', 'date']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Qualys Infrastructure Webgui Parser.\n\n        Fields:\n        - title: Set to title from Qualys Infrastructure Webgui Scanner.\n        - severity: Set to severity from Qualys Infrastructure Webgui Scanner translated into DefectDojo formant.\n\n        NOTE: endpoints is not provided by parser\n        '
        return ['title', 'severity']

    def get_scan_types(self):
        return ['Qualys Infrastructure Scan (WebGUI XML)']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Qualys WebGUI output files can be imported in XML format.'

    def get_findings(self, scan_file, test):
        data = ElementTree.parse(scan_file).getroot()
        scan_date = datetime.now()
        for i in data.findall('HEADER/KEY'):
            if (i.get('value') == 'DATE'):
                scan_date = parser.isoparse(i.text)
        master_list = []
        for issue in data.findall('IP'):
            master_list += issue_r(issue, data, scan_date)
        return master_list
