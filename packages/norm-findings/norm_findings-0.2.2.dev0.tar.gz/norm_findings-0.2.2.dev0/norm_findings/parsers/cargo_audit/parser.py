# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
from norm_findings.stubs.models import Finding

class CargoAuditParser():
    'A class that can be used to parse the cargo audit JSON report file'

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Cargo Audit Parser.\n\n        Fields:\n        - title: Set to the title from Cargo Audit Scanner\n        - severity: Set to "High" regardless of context.\n        - tags: Set to the tags from Cargo Audit Scanner if they are provided.\n        - description: Set to the description from Cargo Audit Scanner and joined with URL provided.\n        - component_name: Set to name of package provided by the Cargo Audit Scanner.\n        - component_version: Set to version of package provided by the Cargo Audit Scanner.\n        - vuln_id_from_tool: Set to id provided by the Cargo Audit Scanner.\n        - publish_date: Set to date provided by the Cargo Audit Scanner.\n        - nb_occurences: Set to 1 by the parser.\n        - mitigation: Set to package_name and versions if information is available.\n\n        NOTE: This parser supports tags\n        '
        return ['title', 'severity', 'tags', 'description', 'component_name', 'component_version', 'vuln_id_from_tool', 'publish_date', 'nb_occurences', 'mitigation']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Cargo Audit Parser.\n\n        Fields:\n        - severity: Set to "High" regardless of context.\n        - component_name: Set to name of package provided by the Cargo Audit Scanner.\n        - component_version: Set to version of package provided by the Cargo Audit Scanner.\n        - vuln_id_from_tool: Set to id provided by the Cargo Audit Scanner.\n\n        NOTE: vulnerability_ids is not provided by parser.\n        NOTE: vulnerability_ids appears to be stored in unsaved_vulnerability_ids.\n        '
        return ['severity', 'component_name', 'component_version', 'vuln_id_from_tool']

    def get_scan_types(self):
        return ['CargoAudit Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'CargoAudit Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import JSON output for cargo audit scan report.'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        dupes = {}
        if data.get('vulnerabilities'):
            for item in data.get('vulnerabilities').get('list'):
                advisory = item.get('advisory')
                vuln_id = advisory.get('id')
                vulnerability_ids = [advisory.get('id')]
                categories = (f"**Categories:** {', '.join(advisory['categories'])}" if ('categories' in advisory) else '')
                description = (categories + f'''
**Description:** `{advisory.get('description')}`''')
                if ((item['affected'] is not None) and ('functions' in item['affected'])):
                    affected_func = [f"{func}: {', '.join(versions)}" for (func, versions) in item['affected']['functions'].items()]
                    description += f'''
**Affected functions**: {', '.join(affected_func)}'''
                references = (f'''{advisory.get('url')}
''' + '\n'.join(advisory['references']))
                date = advisory.get('date')
                for alias in advisory.get('aliases', []):
                    vulnerability_ids.append(alias)
                package_name = item.get('package').get('name')
                package_version = item.get('package').get('version')
                title = f"[{package_name} {package_version}] {advisory.get('title')}"
                severity = 'High'
                tags = (advisory.get('keywords') if ('keywords' in advisory) else [])
                try:
                    mitigation = f"**Update {package_name} to** {', '.join(item['versions']['patched'])}"
                except KeyError:
                    mitigation = 'No information about patched version'
                dupe_key = hashlib.sha256((((vuln_id + date) + package_name) + package_version).encode('utf-8')).hexdigest()
                if (dupe_key in dupes):
                    finding = dupes[dupe_key]
                    finding.nb_occurences += 1
                else:
                    finding = Finding(title=title, test=test, severity=severity, tags=tags, description=description, component_name=package_name, component_version=package_version, vuln_id_from_tool=vuln_id, publish_date=date, nb_occurences=1, references=references, mitigation=mitigation)
                    finding.unsaved_vulnerability_ids = vulnerability_ids
                    dupes[dupe_key] = finding
        return list(dupes.values())
