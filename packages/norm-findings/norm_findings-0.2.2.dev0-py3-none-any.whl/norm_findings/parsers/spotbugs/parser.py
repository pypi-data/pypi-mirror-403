# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import re
import html2text
from defusedxml import ElementTree
from norm_findings.stubs.models import Finding

class SpotbugsParser():
    'Parser for XML ouput file from Spotbugs (https://github.com/spotbugs/spotbugs)'

    def get_scan_types(self):
        return ['SpotBugs Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'XML report of textui cli.'

    def get_findings(self, scan_file, test):
        mitigation_patterns = {}
        reference_patterns = {}
        dupes = {}
        SEVERITY = {'1': 'High', '2': 'Medium', '3': 'Low'}
        tree = ElementTree.parse(scan_file)
        root = tree.getroot()
        html_parser = html2text.HTML2Text()
        html_parser.ignore_links = False
        for pattern in root.findall('BugPattern'):
            html_text = html_parser.handle(ElementTree.tostring(pattern.find('Details'), method='text').decode('utf-8'))
            mitigation = ''
            i = 0
            for line in html_text.splitlines():
                i += 1
                if ('Reference' in line):
                    break
                if (('Vulnerable Code:' in line) or ('Insecure configuration:' in line) or ('Code at risk:' in line)):
                    mitigation += '\n\n#### Example\n'
                mitigation += (line + '\n')
            mitigation_patterns[pattern.get('type')] = mitigation
            reference = ''
            for line in html_text.splitlines()[i:]:
                reference += (line + ' ')
            reference = re.sub('(?<=\\))(.*?)(?=\\[)', '\n', reference)
            reference_patterns[pattern.get('type')] = reference
        for bug in root.findall('BugInstance'):
            desc = ''
            for message in bug.itertext():
                desc += (message + '\n')
            shortmessage_extract = bug.find('ShortMessage')
            title = (shortmessage_extract.text if (shortmessage_extract is not None) else bug.get('type'))
            severity = SEVERITY[bug.get('priority')]
            description = desc
            finding = Finding(title=title, cwe=int(bug.get('cweid', default=0)), severity=severity, description=description, test=test, static_finding=True, dynamic_finding=False, nb_occurences=1)
            source_extract = bug.find('SourceLine')
            if (source_extract is not None):
                finding.file_path = source_extract.get('sourcepath')
                finding.sast_source_object = source_extract.get('classname')
                finding.sast_source_file_path = source_extract.get('sourcepath')
                if (('start' in source_extract.attrib) and source_extract.get('start').isdigit()):
                    finding.line = int(source_extract.get('start'))
                    finding.sast_source_line = int(source_extract.get('start'))
            if (bug.get('type') in mitigation_patterns):
                finding.mitigation = mitigation_patterns[bug.get('type')]
                finding.references = reference_patterns[bug.get('type')]
            if ('instanceHash' in bug.attrib):
                dupe_key = bug.get('instanceHash')
            else:
                dupe_key = f'no_instance_hash|{title}|{description}'
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                find.nb_occurences += 1
            else:
                dupes[dupe_key] = finding
        return list(dupes.values())
