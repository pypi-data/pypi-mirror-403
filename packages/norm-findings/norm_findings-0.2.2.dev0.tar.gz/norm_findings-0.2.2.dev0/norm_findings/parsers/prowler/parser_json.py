# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding

class ProwlerParserJSON():
    'This parser is for Prowler JSON files.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        dupes = {}
        for node in data:
            if (node.get('status_code') == 'PASS'):
                continue
            cloudtype = self.get_cloud_type(node)
            description = ((((((((((((('**Cloud Type** : ' + cloudtype) + '\n\n') + '**Finding Description** : ') + node.get('finding_info', {}).get('desc', 'N/A')) + '\n\n') + '**Product Name** : ') + node.get('metadata', {}).get('product', {}).get('name', 'N/A')) + '\n\n') + '**Status Detail** : ') + node.get('status_detail', 'N/A')) + '\n\n') + '**Finding Created Time** : ') + node.get('finding_info', {}).get('created_time_dt', 'N/A'))
            description = self.add_cloud_type_metadata(node, cloudtype, description)
            title = node.get('message', '')
            severity = self.convert_severity(node.get('severity'))
            mitigation = (((('**Remediation Description** : ' + node.get('remediation', {}).get('desc', 'N/A')) + '\n\n') + '**Remediation References** : ') + ', '.join(node.get('remediation', {}).get('references', [])))
            impact = node.get('risk_details', '')
            compliance = node.get('unmapped', {}).get('compliance', {})
            references = ('**Related URL** : ' + node.get('unmapped', {}).get('related_url', ''))
            for (key, values) in compliance.items():
                joined = ', '.join(values)
                references += f'''

**{key}** : {joined}'''
            finding = Finding(title=title, test=test, description=description, severity=severity, references=references, mitigation=mitigation, impact=impact, static_finding=False, dynamic_finding=True)
            dupe_key = hashlib.sha256(str((description + title)).encode('utf-8')).hexdigest()
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                if finding.description:
                    find.description += ('\n' + finding.description)
                dupes[dupe_key] = find
            else:
                dupes[dupe_key] = finding
        return list(dupes.values())

    def convert_severity(self, severity: str) -> str:
        'Convert severity value'
        if (not severity):
            return 'Info'
        s = severity.lower()
        if (s == 'critical'):
            return 'Critical'
        if (s == 'high'):
            return 'High'
        if (s == 'medium'):
            return 'Medium'
        if (s == 'low'):
            return 'Low'
        return 'Info'

    def get_cloud_type(self, node: dict) -> str:
        'Determine the cloud type of a Prowler JSON finding. Returns one of: AWS, Azure, Kubernetes, GCP, or N/A'
        account_type = node.get('cloud', {}).get('provider')
        if account_type:
            account_type.lower()
            if (account_type == 'gcp'):
                return 'GCP'
            if (account_type == 'aws'):
                return 'AWS'
            if (account_type == 'azure'):
                return 'AZURE'
        for resource in node.get('resources', []):
            namespace = resource.get('data', {}).get('metadata', {}).get('namespace')
            if (namespace is not None):
                return 'KUBERNETES'
        return 'N/A'

    def add_cloud_type_metadata(self, node: dict, cloudtype: str, description: str) -> str:
        if (cloudtype in {'GCP', 'AWS', 'AZURE'}):
            description += (((('\n\n' + '**') + cloudtype) + ' Region** : ') + node.get('cloud', {}).get('region', 'N/A'))
            return description
        if (cloudtype == 'KUBERNETES'):
            for resource in node.get('resources', []):
                pod = resource.get('data', {}).get('metadata', {}).get('name')
                namespace = resource.get('data', {}).get('metadata', {}).get('namespace')
                if (pod is not None):
                    description += (('\n\n' + '**Pod Name** : ') + pod)
                if (namespace is not None):
                    description += (('\n\n' + '**Namespace** : ') + namespace)
                return description
        return description
