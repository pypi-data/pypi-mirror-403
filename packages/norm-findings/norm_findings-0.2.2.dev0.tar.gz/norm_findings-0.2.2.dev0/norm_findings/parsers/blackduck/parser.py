# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
from norm_findings.stubs.models import Finding
from .importer import BlackduckImporter

class BlackduckParser():
    '\n    Can import as exported from Blackduck:\n    - from a zip file containing a security.csv and files.csv\n    - a single security.csv file\n    '

    def get_scan_types(self):
        return ['Blackduck Hub Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Blackduck Hub Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Upload the zip file containing the security.csv and components.csv for Security and License risks.'

    def get_findings(self, scan_file, test):
        normalized_findings = self.normalize_findings(scan_file)
        return self.ingest_findings(normalized_findings, test)

    def normalize_findings(self, filename):
        importer = BlackduckImporter()
        return sorted(importer.parse_findings(filename), key=(lambda f: f.vuln_id))

    def ingest_findings(self, normalized_findings, test):
        dupes = {}
        for i in normalized_findings:
            vulnerability_id = i.vuln_id
            cwe = 0
            title = self.format_title(i)
            description = self.format_description(i)
            severity = str(i.security_risk.title())
            mitigation = self.format_mitigation(i)
            impact = i.impact
            references = self.format_reference(i)
            dupe_key = hashlib.md5(f'{title} | {i.vuln_source}'.encode(), usedforsecurity=False).hexdigest()
            if (dupe_key in dupes):
                finding = dupes[dupe_key]
                if finding.description:
                    finding.description += f'''Vulnerability ID: {vulnerability_id}
 {i.vuln_source}
'''
                dupes[dupe_key] = finding
            else:
                dupes[dupe_key] = True
                finding = Finding(title=title, cwe=int(cwe), test=test, description=description, severity=severity, mitigation=mitigation, impact=impact, references=references, url=i.url, file_path=i.locations, component_name=i.component_name, component_version=i.component_version, static_finding=True)
                if vulnerability_id:
                    finding.unsaved_vulnerability_ids = [vulnerability_id]
                dupes[dupe_key] = finding
        return list(dupes.values())

    def format_title(self, i):
        if (i.channel_version_origin_id is not None):
            component_title = i.channel_version_origin_id
        else:
            component_title = i.component_origin_id
        return f'{i.vuln_id} - {component_title}'

    def format_description(self, i):
        description = f'''Published on: {i.published_date}

'''
        description += f'''Updated on: {i.updated_date}

'''
        description += f'''Base score: {i.base_score}

'''
        description += f'''Exploitability: {i.exploitability}

'''
        description += f'''Description: {i.description}
'''
        return description

    def format_mitigation(self, i):
        mitigation = f'''Remediation status: {i.remediation_status}
'''
        mitigation += f'''Remediation target date: {i.remediation_target_date}
'''
        mitigation += f'''Remediation actual date: {i.remediation_actual_date}
'''
        mitigation += f'''Remediation comment: {i.remediation_comment}
'''
        return mitigation

    def format_reference(self, i):
        reference = f'''Source: {i.vuln_source}
'''
        reference += f'''URL: {i.url}
'''
        return reference
