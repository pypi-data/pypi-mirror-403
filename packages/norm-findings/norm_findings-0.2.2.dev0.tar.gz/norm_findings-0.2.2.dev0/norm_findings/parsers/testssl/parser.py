# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import csv
import hashlib
import io
from norm_findings.stubs.models import Endpoint, Finding

class TestsslParser():

    def get_scan_types(self):
        return ['Testssl Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Testssl Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import CSV output of testssl scan report.'

    def get_findings(self, scan_file, test):
        content = scan_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content), delimiter=',', quotechar='"')
        dupes = {}
        for row in reader:
            if (row['severity'] == 'OK'):
                continue
            if (row['id'] in {'rating_spec', 'rating_doc', 'protocol_support_score', 'protocol_support_score_weighted', 'key_exchange_score', 'key_exchange_score_weighted', 'cipher_strength_score', 'cipher_strength_score_weighted', 'final_score', 'overall_grade'}):
                continue
            if ('grade_cap_reason_' in row['id']):
                continue
            severity = row['severity'].lower().capitalize()
            if (severity in {'Warn', 'Fatal'}):
                severity = 'Info'
            cves = row['cve'].split(' ')
            if (len(cves) == 0):
                cves = [None]
            for vulnerability in cves:
                finding = Finding(title=row['id'], description=row['finding'], severity=severity, nb_occurences=1)
                if ('cipher-tls' in row['id']):
                    ciphertls = ('TLS_' + row['finding'].split('TLS_')[1])
                    finding.references = (((('[https://ciphersuite.info/cs/' + ciphertls) + '](https://ciphersuite.info/cs/') + ciphertls) + ')')
                if vulnerability:
                    finding.unsaved_vulnerability_ids = [vulnerability]
                if ('-' in row['cwe']):
                    finding.cwe = int(row['cwe'].split('-')[1].strip())
                finding.unsaved_endpoints = [Endpoint(host=row['fqdn/ip'].split('/')[0])]
                if (row.get('port') and row['port'].isdigit()):
                    finding.unsaved_endpoints[0].port = int(row['port'])
                dupe_key = hashlib.sha256('|'.join([finding.description, finding.title, str(vulnerability)]).encode('utf-8')).hexdigest()
                if (dupe_key in dupes):
                    dupes[dupe_key].unsaved_endpoints.extend(finding.unsaved_endpoints)
                    if dupes[dupe_key].unsaved_vulnerability_ids:
                        dupes[dupe_key].unsaved_vulnerability_ids.extend(finding.unsaved_vulnerability_ids)
                    else:
                        dupes[dupe_key].unsaved_vulnerability_ids = finding.unsaved_vulnerability_ids
                    dupes[dupe_key].nb_occurences += finding.nb_occurences
                else:
                    dupes[dupe_key] = finding
        return list(dupes.values())
