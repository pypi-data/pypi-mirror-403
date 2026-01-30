# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import hashlib
import logging
from defusedxml import ElementTree
from norm_findings.stubs.models import Endpoint, Finding
LOGGER = logging.getLogger(__name__)

class IbmAppParser():

    def get_scan_types(self):
        return ['IBM AppScan DAST']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'XML file from IBM App Scanner.'

    def get_findings(self, scan_file, test):
        ibm_scan_tree = ElementTree.parse(scan_file)
        root = ibm_scan_tree.getroot()
        if ('xml-report' not in root.tag):
            msg = 'This does not look like a valid expected Ibm AppScan DAST XML file.'
            raise ValueError(msg)
        issue_types = self.fetch_issue_types(root)
        dupes = {}
        for issue in root.iter('issue-group'):
            for item in issue.iter('item'):
                ref_link = ''
                if (item.find('issue-type/ref') is not None):
                    recommendation_data = ''
                    issue_data = issue_types[item.find('issue-type/ref').text]
                    name = issue_data['name']
                    vulnerability_id = issue_data.get('cve')
                    cwe = issue_data.get('cwe')
                    if cwe:
                        cwe = int(cwe)
                    url = self.get_url(root, item.find('url/ref').text)
                    severity = item.find('severity').text.capitalize()
                    if (severity == 'Informational'):
                        severity = 'Info'
                    issue_description = self.fetch_advisory_group(root, issue_data['advisory'])
                    for fix_recommendation_group in root.iter('fix-recommendation-group'):
                        for recommendation in fix_recommendation_group.iter('item'):
                            if (recommendation.attrib['id'] == issue_data['fix-recommendation']):
                                data = recommendation.find('general/fixRecommendation')
                                for data_text in data.iter('text'):
                                    recommendation_data += (data_text.text + '\n')
                                for link in data.iter('link'):
                                    if (link is not None):
                                        ref_link += (link.text + '\n')
                    dupe_key = hashlib.md5(str(((issue_description + name) + severity)).encode('utf-8'), usedforsecurity=False).hexdigest()
                    if (dupe_key in dupes):
                        finding = dupes[dupe_key]
                        if (issue_description is not None):
                            finding.description += issue_description
                    else:
                        finding = Finding(title=name, test=test, cwe=cwe, description=issue_description, severity=severity, mitigation=recommendation_data, references=ref_link, dynamic_finding=True)
                        if vulnerability_id:
                            finding.unsaved_vulnerability_ids = [vulnerability_id]
                        if recommendation_data:
                            finding.fix_available = True
                        else:
                            finding.fix_available = False
                        finding.unsaved_endpoints = []
                        dupes[dupe_key] = finding
                        if url:
                            finding.unsaved_endpoints.append(Endpoint.from_uri(url))
        return list(dupes.values())

    def fetch_issue_types(self, root):
        issues = {}
        for issue_type in root.iter('issue-type-group'):
            for item in issue_type.iter('item'):
                issues[item.attrib['id']] = {'name': item.find('name').text, 'advisory': item.find('advisory/ref').text, 'fix-recommendation': item.find('fix-recommendation/ref').text}
                cve = item.find('cve').text
                if (cve is not None):
                    issues[item.attrib['id']]['cve'] = cve
                cwe = item.find('cwe/link')
                if (cwe is None):
                    cwe = item.find('cwe')
                if (cwe.text is not None):
                    issues[item.attrib['id']]['cwe'] = int(cwe.text)
        return issues

    def fetch_advisory_group(self, root, advisory):
        "Function that parse advisory-group in order to get the item's description"
        for advisory_group in root.iter('advisory-group'):
            for item in advisory_group.iter('item'):
                if (item.attrib['id'] == advisory):
                    return item.find('advisory/testTechnicalDescription/text').text
        return 'N/A'

    def get_url(self, root, ref):
        for url_group in root.iter('url-group'):
            for item in url_group.iter('item'):
                if (item.attrib['id'] == ref):
                    return item.find('name').text
        return None
