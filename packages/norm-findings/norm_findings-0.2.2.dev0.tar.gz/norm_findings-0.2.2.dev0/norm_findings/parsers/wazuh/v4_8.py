# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from norm_findings.stubs.models import Finding

class WazuhV4_8():

    def parse_findings(self, test, data):
        dupes = {}
        vulnerabilities = data.get('hits', {}).get('hits', [])
        for item_source in vulnerabilities:
            item = item_source.get('_source')
            vuln = item.get('vulnerability')
            cve = vuln.get('id')
            dupe_key = f"{cve}-{item.get('agent', {}).get('id')}"
            if (dupe_key in dupes):
                continue
            description = vuln.get('description')
            description += ('\nAgent id:' + item.get('agent').get('id'))
            description += ('\nAgent name:' + item.get('agent').get('name'))
            severity = vuln.get('severity')
            cvssv3_score = vuln.get('score').get('base')
            publish_date = vuln.get('published_at').split('T')[0]
            detection_time = vuln.get('detected_at').split('T')[0]
            references = vuln.get('reference')
            SEVERITY_MAP = {'Critical': 'Critical', 'High': 'High', 'Medium': 'Medium', 'Low': 'Low', 'Info': 'Info', 'Informational': 'Info', 'Untriaged': 'Info'}
            severity = SEVERITY_MAP.get(severity, 'Info')
            title = (((cve + ' affects (version: ') + item.get('package').get('version')) + ')')
            find = Finding(title=title, test=test, description=description, severity=severity, references=references, static_finding=True, component_name=item.get('package').get('name'), component_version=item.get('package').get('version'), cvssv3_score=cvssv3_score, publish_date=publish_date, unique_id_from_tool=dupe_key, date=detection_time)
            find.unsaved_vulnerability_ids = [cve]
            dupes[dupe_key] = find
        return list(dupes.values())
