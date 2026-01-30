# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import json
import dateutil
from netaddr import IPAddress
from norm_findings.stubs.models import Endpoint, Finding
SEVERITY_MAPPING = {'INFORMATIONAL': 'Info', 'LOW': 'Low', 'MEDIUM': 'Medium', 'HIGH': 'High', 'CRITICAL': 'Critical'}

class AsffParser():

    def get_scan_types(self):
        return ['AWS Security Finding Format (ASFF) Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'AWS Security Finding Format (ASFF)'

    def get_description_for_scan_types(self, scan_type):
        return 'AWS Security Finding Format (ASFF).\n        https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings-format-syntax.html'

    def get_item_resource_arns(self, item):
        resource_arns = []
        if isinstance(item.get('Resources'), list):
            for resource_block in item['Resources']:
                if isinstance(resource_block, dict):
                    resource_id = resource_block.get('Id')
                    if resource_id:
                        resource_arns.append(resource_id)
        return resource_arns

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        result = []
        for item in data:
            if item.get('Remediation'):
                mitigation = item.get('Remediation').get('Recommendation').get('Text')
                references = item.get('Remediation').get('Recommendation').get('Url')
            else:
                mitigation = None
                references = None
            active = bool((item.get('RecordState') and (item.get('RecordState') == 'ACTIVE')))
            resource_arns = self.get_item_resource_arns(item)
            control_description = item.get('Description')
            if resource_arns:
                resource_arn_strings = ', '.join(resource_arns)
                full_description = f'''**AWS resource ARN:** {resource_arn_strings}

{control_description}'''
                impact = resource_arn_strings
            else:
                full_description = control_description
                impact = None
            finding = Finding(title=item.get('Title'), description=full_description, date=dateutil.parser.parse(item.get('CreatedAt')), mitigation=mitigation, references=references, severity=self.get_severity(item.get('Severity')), active=active, unique_id_from_tool=item.get('Id'), impact=impact)
            if ('Resources' in item):
                endpoints = []
                for resource in item['Resources']:
                    if ((resource['Type'] == 'AwsEc2Instance') and ('Details' in resource)):
                        details = resource['Details']['AwsEc2Instance']
                        endpoints.extend((Endpoint(host=ip) for ip in details.get('IpV4Addresses', []) if (not IPAddress(ip).is_global())))
                finding.unsaved_endpoints = endpoints
            result.append(finding)
        return result

    def get_severity(self, data):
        if data.get('Label'):
            return SEVERITY_MAPPING[data.get('Label')]
        if isinstance(data.get('Normalized'), int):
            if (data.get('Normalized') > 89):
                return 'Critical'
            if (data.get('Normalized') > 69):
                return 'High'
            if (data.get('Normalized') > 39):
                return 'Medium'
            if (data.get('Normalized') > 0):
                return 'Low'
            return 'Info'
        return None
