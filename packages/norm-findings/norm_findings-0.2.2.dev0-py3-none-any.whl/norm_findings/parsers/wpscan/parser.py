# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import datetime
import hashlib
import json
from norm_findings.stubs.models import Endpoint, Finding

class WpscanParser():
    'WPScan - WordPress Security Scanner'

    def get_scan_types(self):
        return ['Wpscan']

    def get_label_for_scan_types(self, scan_type):
        return 'Wpscan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import JSON report'

    def get_vulnerabilities(self, report_date, vulnerabilities, dupes, node=None, plugin=None, detection_confidence=None):
        for vul in vulnerabilities:
            description = '\n'.join([(('**Title:** `' + vul['title']) + '`\n')])
            if (node and ('location' in node)):
                description += (('**Location:** `' + ''.join(node['location'])) + '`\n')
            if plugin:
                description += (('**Plugin:** `' + ''.join(plugin)) + '`\n')
            finding = Finding(title=vul['title'], description=description, severity='Medium', cwe=1035, references=self.generate_references(vul['references']), dynamic_finding=True, static_finding=False, scanner_confidence=self._get_scanner_confidence(detection_confidence), unique_id_from_tool=vul['references']['wpvulndb'][0], nb_occurences=1)
            if plugin:
                finding.component_name = plugin
            if (node and ('version' in node) and (node['version'] is not None)):
                finding.component_version = node['version'].get('number')
            if report_date:
                finding.date = report_date
            finding.fix_available = False
            if vul.get('fixed_in'):
                finding.mitigation = ('fixed in : ' + vul['fixed_in'])
                finding.fix_available = True
            if ('cve' in vul['references']):
                finding.unsaved_vulnerability_ids = []
                for vulnerability_id in vul['references']['cve']:
                    finding.unsaved_vulnerability_ids.append(f'CVE-{vulnerability_id}')
            dupe_key = hashlib.sha256(str(finding.unique_id_from_tool).encode('utf-8')).hexdigest()
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                if finding.references:
                    dupes[dupe_key].references += finding.references
                find.nb_occurences += finding.nb_occurences
            else:
                dupes[dupe_key] = finding

    def get_findings(self, scan_file, test):
        tree = json.load(scan_file)
        report_date = None
        if ('start_time' in tree):
            report_date = datetime.datetime.fromtimestamp(tree.get('start_time'), datetime.timezone.utc)
        dupes = {}
        for plugin in tree.get('plugins', []):
            node = tree['plugins'][plugin]
            self.get_vulnerabilities(report_date, node.get('vulnerabilities'), dupes, node, plugin, detection_confidence=node.get('confidence'))
        if tree.get('version'):
            if (('vulnerabilities' in tree['version']) and tree['version']['vulnerabilities']):
                self.get_vulnerabilities(report_date, tree['version']['vulnerabilities'], dupes, node=None, plugin=None, detection_confidence=tree['version'].get('confidence'))
        for interesting_finding in tree.get('interesting_findings', []):
            references = self.generate_references(interesting_finding['references'])
            description = '\n'.join([(('**Type:** `' + interesting_finding.get('type')) + '`\n'), (('**Url:** `' + interesting_finding['url']) + '`\n')])
            if interesting_finding['interesting_entries']:
                description += (('**Details:** `' + ' '.join(interesting_finding['interesting_entries'])) + '`\n')
            finding = Finding(title=f"Interesting finding: {interesting_finding.get('to_s')}", description=description, references=references, severity='Info', dynamic_finding=True, static_finding=False, scanner_confidence=self._get_scanner_confidence(interesting_finding.get('confidence')))
            endpoint = Endpoint.from_uri(interesting_finding['url'])
            finding.unsaved_endpoints = [endpoint]
            if report_date:
                finding.date = report_date
            dupe_key = hashlib.sha256(str((('interesting_findings' + finding.title) + interesting_finding['url'])).encode('utf-8')).hexdigest()
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                if finding.references:
                    dupes[dupe_key].references += finding.references
                find.nb_occurences += finding.nb_occurences
            else:
                dupes[dupe_key] = finding
        return list(dupes.values())

    def generate_references(self, node):
        references = ''
        for ref in node:
            for item in node.get(ref, []):
                if (ref == 'url'):
                    references += f'''* [{item}]({item})
'''
                elif (ref == 'wpvulndb'):
                    references += f'''* [WPScan WPVDB](https://wpscan.com/vulnerability/{item})
'''
                else:
                    references += f'''* {item} - {ref}
'''
        return references

    def _get_scanner_confidence(self, val):
        '\n        Confidence value are from 0 (wrong) to 100 (certain)\n        So we divide by 10 and invert axis\n        '
        if (val is None):
            return None
        val_raw = round((int(val) / 10))
        return (10 - val_raw)
