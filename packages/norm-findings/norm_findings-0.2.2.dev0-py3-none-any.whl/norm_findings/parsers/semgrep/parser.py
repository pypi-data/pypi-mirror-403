# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
from norm_findings.stubs.models import Finding

class SemgrepParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Semgrep Parser.\n\n        Fields:\n        - title: Set to the check_id value outputted by the Semgrep Scanner.\n        - severity: Set to severity from Semgrep Scanner that has been converted to DefectDojo format.\n        - description: Custom description made from elements outputted by Semgrep Scanner.\n        - file_path: Set to filepath from Semgrep Scanner.\n        - line: Set to line from Semgrep Scanner.\n        - static_finding: Set to true.\n        - dynamic_finding: Set to false.\n        - vuln_id_from_tool: Set to Vuln Id from Semgrep Scanner.\n        - nb_occurences: Initially set to 1 then updated.\n        - unique_id_from_tool: Set to corresponding field from scanner if it is present in the output.\n        - cwe: Set to cwe from scanner output if present.\n        - mitigation: Set to "fix" from scanner output or "fix_regex" if "fix" isn\'t present.\n        '
        return ['title', 'severity', 'description', 'file_path', 'line', 'static_finding', 'dynamic_finding', 'vuln_id_from_tool', 'nb_occurences', 'unique_id_from_tool', 'cwe', 'mitigation']

    def get_dedupe_fields(self) -> list[str]:
        "\n        Return the list of fields used for deduplication in the Semgrep Parser.\n\n        Fields:\n        - title: Set to the title outputted by the Semgrep Scanner.\n        - cwe: Set to cwe from scanner output if present.\n        - line: Set to line from Semgrep Scanner.\n        - file_path: Set to filepath from Semgrep Scanner.\n        - description: Custom description made from elements outputted by Semgrep Scanner.\n\n        NOTE: uses legacy dedupe: ['title', 'cwe', 'line', 'file_path', 'description']\n        "
        return ['title', 'cwe', 'line', 'file_path', 'description']

    def get_scan_types(self):
        return ['Semgrep JSON Report']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Semgrep output (--json)'

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        dupes = {}
        if ('results' in data):
            for item in data.get('results', []):
                finding = Finding(test=test, title=item.get('check_id'), severity=self.convert_severity(item['extra']['severity']), description=self.get_description(item), file_path=item['path'], line=item['start']['line'], static_finding=True, dynamic_finding=False, vuln_id_from_tool=item['check_id'], nb_occurences=1)
                unique_id_from_tool = item.get('extra', {}).get('fingerprint')
                if (unique_id_from_tool == 'requires login'):
                    unique_id_from_tool = None
                if unique_id_from_tool:
                    finding.unique_id_from_tool = unique_id_from_tool
                if ('cwe' in item['extra']['metadata']):
                    if isinstance(item['extra']['metadata'].get('cwe'), list):
                        finding.cwe = int(item['extra']['metadata'].get('cwe')[0].partition(':')[0].partition('-')[2])
                    else:
                        finding.cwe = int(item['extra']['metadata'].get('cwe').partition(':')[0].partition('-')[2])
                if ('references' in item['extra']['metadata']):
                    finding.references = '\n'.join(item['extra']['metadata']['references'])
                if ('fix' in item['extra']):
                    finding.mitigation = item['extra']['fix']
                elif ('fix_regex' in item['extra']):
                    finding.mitigation = '\n'.join(['**You can automaticaly apply this regex:**', '\n```\n', json.dumps(item['extra']['fix_regex']), '\n```\n'])
                dupe_key = ((finding.title + finding.file_path) + str(finding.line))
                if (dupe_key in dupes):
                    find = dupes[dupe_key]
                    find.nb_occurences += 1
                else:
                    dupes[dupe_key] = finding
        elif ('vulns' in data):
            for item in data.get('vulns', []):
                finding = Finding(test=test, title=item.get('title'), severity=self.convert_severity(item['advisory']['severity']), description=item.get('advisory', {}).get('description'), file_path=item['dependencyFileLocation']['path'], line=item['dependencyFileLocation']['startLine'], static_finding=True, dynamic_finding=False, vuln_id_from_tool=item['repositoryId'], nb_occurences=1)
                unique_id_from_tool = item.get('extra', {}).get('fingerprint')
                if (unique_id_from_tool == 'requires login'):
                    unique_id_from_tool = None
                if unique_id_from_tool:
                    finding.unique_id_from_tool = unique_id_from_tool
                if ('cweIds' in item['advisory']['references']):
                    if isinstance(item['advisory']['references'].get('cweIds'), list):
                        finding.cwe = int(item['advisory']['references'].get('cweIds')[0].partition(':')[0].partition('-')[2])
                    else:
                        finding.cwe = int(item['advisory']['references'].get('cweIds').partition(':')[0].partition('-')[2])
                dupe_key = ((finding.title + finding.file_path) + str(finding.line))
                if (dupe_key in dupes):
                    find = dupes[dupe_key]
                    find.nb_occurences += 1
                else:
                    dupes[dupe_key] = finding
        return list(dupes.values())

    def convert_severity(self, val):
        upper_value = val.upper()
        if (upper_value == 'CRITICAL'):
            return 'Critical'
        if (upper_value in {'WARNING', 'MEDIUM'}):
            return 'Medium'
        if (upper_value in {'ERROR', 'HIGH'}):
            return 'High'
        if (upper_value in {'LOW', 'INFO'}):
            return 'Low'
        msg = f'Unknown value for severity: {val}'
        raise ValueError(msg)

    def get_description(self, item):
        description = ''
        message = item['extra']['message']
        description += f'''**Result message:** {message}
'''
        snippet = item['extra'].get('lines')
        if (snippet == 'requires login'):
            snippet = None
        if (snippet is not None):
            if ('<![' in snippet):
                snippet = snippet.replace('<![', '<! [')
                description += f'''**Snippet:** ***Caution:*** Please remove the space between `!` and `[` to have the real value due to a workaround to circumvent [#8435](https://github.com/DefectDojo/django-DefectDojo/issues/8435).
```{snippet}```
'''
            else:
                description += f'''**Snippet:**
```{snippet}```
'''
        return description
