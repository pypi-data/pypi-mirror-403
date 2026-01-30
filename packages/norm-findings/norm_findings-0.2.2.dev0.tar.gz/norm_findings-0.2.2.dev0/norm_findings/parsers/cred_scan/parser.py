# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import csv
import io
from dateutil import parser
from norm_findings.stubs.models import Finding

class CredScanParser():
    '\n    Credential Scanner (aka CredScan) is a tool developed and maintained by\n    Microsoft to identify credential leaks such as those in source code and\n    configuration files. Some of the commonly found types of credentials are\n    default passwords, SQL connection strings and Certificates with private keys.\n    See: https://secdevtools.azurewebsites.net/helpcredscan.html\n    '

    def get_scan_types(self):
        return ['CredScan Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'CredScan Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import CSV output of CredScan scan report.'

    def get_findings(self, scan_file, test):
        content = scan_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content), delimiter=',', quotechar='"')
        dupes = {}
        for row in reader:
            description = row.get('Description', 'Description not provided')
            if ('IsSuppressed' in row):
                description += ('\n Is Supressed: ' + str(row['IsSuppressed']))
            if ('SuppressJustification' in row):
                description += ('\n Supress Justifcation: ' + str(row['SuppressJustification']))
            if ('MatchingScore' in row):
                description += ('\n Matching Score: ' + str(row['MatchingScore']))
            finding = Finding(title=row['Searcher'], description=description, severity='Info', nb_occurences=1, file_path=row['Source'], line=row['Line'])
            if ('TimeofDiscovery' in row):
                finding.date = parser.parse(row['TimeofDiscovery'].replace('Z', ''))
            dupe_key = ((row['Searcher'] + row['Source']) + str(row['Line']))
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                find.nb_occurences += finding.nb_occurences
            else:
                dupes[dupe_key] = finding
        return list(dupes.values())
