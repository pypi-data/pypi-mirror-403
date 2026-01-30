# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Test, Finding

import csv
import io
from norm_findings.stubs.models import Finding, Test

class ZoraParser():
    'Parser for Zora combined CSV export.'

    def get_scan_types(self):
        return ['Zora Parser']

    def get_label_for_scan_types(self, scan_type):
        return 'Zora Parser'

    def get_description_for_scan_types(self, scan_type):
        return 'Zora Parser scan results in csv file format.'

    def get_findings(self, scan_file, test: Test) -> list[Finding]:
        findings = []
        if hasattr(scan_file, 'read'):
            scan_file = scan_file.read()
        if isinstance(scan_file, bytes):
            scan_file = scan_file.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(scan_file), delimiter=',', quotechar='"')
        for row in csv_reader:
            title = row.get('title')
            raw_severity = (row.get('severity') or '').strip().lower()
            severity_map = {'info': 'Info', 'informational': 'Info', 'low': 'Low', 'medium': 'Medium', 'med': 'Medium', 'high': 'High', 'critical': 'Critical', 'crit': 'Critical'}
            severity = severity_map.get(raw_severity, 'Info')
            description = f'''**Source**: {row.get('source')}
'''
            description += f'''**Image**: {row.get('image')}
'''
            description += f'''**ID**: {row.get('id')}
'''
            description += f'''**Details**: {row.get('description')}
'''
            mitigation = row.get('description', '')
            unique_id = f"{row.get('source')}-{row.get('image')}-{row.get('id')}"
            status = row.get('status', '').upper()
            is_mitigated = (status in {'PASS', 'OK', 'FIXED'})
            finding = Finding(title=title, description=description, severity=severity, mitigation=mitigation, static_finding=False, dynamic_finding=True, unique_id_from_tool=unique_id, test=test, is_mitigated=is_mitigated)
            if row.get('fixVersion'):
                finding.fix_available = True
                finding.fix_version = row.get('fixVersion')
            else:
                finding.fix_available = False
            vuln_id = row.get('id')
            if vuln_id:
                finding.unsaved_vulnerability_ids = [vuln_id]
            findings.append(finding)
        return findings
