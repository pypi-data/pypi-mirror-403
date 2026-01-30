# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Test, Endpoint, Finding

import contextlib
import csv
import io
import logging
import re
import sys
from cpe import CPE
from cvss import CVSS3
from norm_findings.stubs.models import Endpoint, Finding, Test
LOGGER = logging.getLogger(__name__)

class TenableCSVParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Tenable CSV Parser\n\n        Fields:\n        - title: Made using the name, plugin name, and asset name from Tenable scanner.\n        - description: Made by combining synopsis and plugin output from Tenable Scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - mitigation: Set to solution from Tenable Scanner.\n        - impact: Set to definition description from Tenable Scanner.\n        - cvssv3: If present, set to cvssv3 from Tenable scanner.\n        - component_name: If present, set to product name from Tenable Scanner.\n        - component_version: If present, set to version from Tenable Scanner.\n        '
        return ['title', 'description', 'severity', 'mitigation', 'impact', 'cvssv3', 'component_name', 'component_version']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of dedupe fields used in the Tenable CSV Parser\n\n        Fields:\n        - title: Made using the name, plugin name, and asset name from Tenable scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - description: Made by combining synopsis and plugin output from Tenable Scanner.\n\n        NOTE: vulnerability_ids & cwe are not provided by parser\n        '
        return ['title', 'severity', 'description']

    def _validated_severity(self, severity):
        if (severity not in Finding.SEVERITIES):
            severity = 'Info'
        return severity

    def _int_severity_conversion(self, severity_value):
        'Convert data of the report into severity'
        severity = 'Info'
        if (severity_value == 4):
            severity = 'Critical'
        elif (severity_value == 3):
            severity = 'High'
        elif (severity_value == 2):
            severity = 'Medium'
        elif (severity_value == 1):
            severity = 'Low'
        return self._validated_severity(severity)

    def _string_severity_conversion(self, severity_value):
        'Convert data of the report into severity'
        if ((severity_value is None) or (len(severity_value) == 0)):
            return 'Info'
        severity = severity_value.title()
        return self._validated_severity(severity)

    def _convert_severity(self, severity_value):
        if isinstance(severity_value, int):
            return self._int_severity_conversion(severity_value)
        if isinstance(severity_value, str):
            return self._string_severity_conversion(severity_value)
        return 'Info'

    def _format_cve(self, val):
        if ((val is None) or (not val)):
            return None
        cve_match = re.findall('CVE-[0-9]+-[0-9]+', val.upper(), re.IGNORECASE)
        if cve_match:
            return cve_match
        return None

    def _format_cpe(self, val):
        if ((val is None) or (not val)):
            return None
        cpe_match = re.findall('cpe:/[^\\n\\ ]+', val)
        return (cpe_match or None)

    def detect_delimiter(self, content: str):
        'Detect the delimiter of the CSV file'
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        first_line = content.split('\n')[0]
        if (';' in first_line):
            return ';'
        return ','

    def get_findings(self, scan_file: str, test: Test):
        content = scan_file.read()
        delimiter = self.detect_delimiter(content)
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        csv.field_size_limit(int((sys.maxsize / 10)))
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        if (('Name' not in reader.fieldnames) and ('Plugin Name' not in reader.fieldnames) and ('asset.name' not in reader.fieldnames)):
            msg = "Invalid CSV file: missing 'Name', 'Plugin Name' or 'asset.name' field"
            raise ValueError(msg)
        dupes = {}
        for row in reader:
            title = row.get('Name', row.get('Plugin Name', row.get('asset.name')))
            if ((title is None) or (not title)):
                continue
            raw_severity = row.get('Risk', row.get('severity', ''))
            if (not raw_severity):
                raw_severity = row.get('Severity', 'Info')
            with contextlib.suppress(ValueError):
                int_severity = int(raw_severity)
                raw_severity = int_severity
            severity = self._convert_severity(raw_severity)
            epss_score = None
            epss_score_string = (row.get('EPSS Score') if ('EPSS Score' in row) else None)
            if epss_score_string:
                if ('0.' not in epss_score_string):
                    epss_score_string = ('0.' + epss_score_string)
                epss_score = float(epss_score_string)
            description = row.get('Synopsis', row.get('definition.synopsis', 'N/A'))
            severity_justification = f'''Severity: {severity}
'''
            for field in ('VPR score', 'EPSS Score', 'Risk Factor', 'STIG Severity', 'CVSS v4.0 Base Score', 'CVSS v4.0 Base+Threat Score', 'CVSS v3.0 Base Score', 'CVSS v3.0 Temporal Score', 'Metasploit', 'Core Impact', 'CANVAS', 'XREF'):
                severity_justification += f'''{field}: {row.get(field, 'N/A')}
'''
            mitigation = str(row.get('Solution', row.get('definition.solution', row.get('Steps to Remediate', 'N/A'))))
            impact = row.get('Description', row.get('definition.description', 'N/A'))
            references = ''
            references += (row.get('References') if ('References' in row) else '')
            references += row.get('See Also', row.get('definition.see_also', 'N/A'))
            references += ('\nTenable Plugin ID: ' + row.get('Plugin', 'N/A'))
            references += ('\nPlugin Information: ' + row.get('Plugin Information', 'N/A'))
            references += ('\nPlugin Publication Date: ' + row.get('Plugin Publication Date', 'N/A'))
            references += ('\nPlugin Modification Date: ' + row.get('Plugin Modification Date', 'N/A'))
            dupe_key = ((((severity + title) + row.get('Host', row.get('asset.host_name', 'No host'))) + str(row.get('Port', row.get('asset.port', 'No port')))) + row.get('Synopsis', row.get('definition.synopsis', 'No synopsis')))
            if (dupe_key not in dupes):
                find = Finding(title=title, test=test, description=description, severity=severity, epss_score=epss_score, mitigation=mitigation, impact=impact, references=references, severity_justification=severity_justification)
                cvss_vector = row.get('CVSS V3 Vector', '')
                if cvss_vector:
                    find.cvssv3 = CVSS3(('CVSS:3.0/' + str(cvss_vector))).clean_vector(output_prefix=True)
                cvssv3 = row.get('CVSSv3', row.get('definition.cvss3.base_score', ''))
                if cvssv3:
                    find.cvssv3_score = cvssv3
                detected_cpe = self._format_cpe(str(row.get('CPE', row.get('definition.cpe', ''))))
                if detected_cpe:
                    if (len(detected_cpe) > 1):
                        LOGGER.debug('more than one CPE for a finding. NOT supported by Nessus CSV parser')
                    try:
                        cpe_decoded = CPE(detected_cpe[0])
                        find.component_name = (cpe_decoded.get_product()[0] if (len(cpe_decoded.get_product()) > 0) else None)
                        find.component_version = (cpe_decoded.get_version()[0] if (len(cpe_decoded.get_version()) > 0) else None)
                    except Exception as e:
                        LOGGER.debug(f"Failed to parse CPE '{detected_cpe[0]}': {e}. Skipping component_name and component_version.")
                find.unsaved_endpoints = []
                find.unsaved_vulnerability_ids = []
                dupes[dupe_key] = find
            else:
                find = dupes[dupe_key]
            plugin_output = str(row.get('Plugin Output', row.get('output', '')))
            if plugin_output:
                find.description += f'''

{plugin_output}'''
            detected_cve = self._format_cve(str(row.get('CVE', row.get('definition.cve', ''))))
            if detected_cve:
                if isinstance(detected_cve, list):
                    find.unsaved_vulnerability_ids += detected_cve
                else:
                    find.unsaved_vulnerability_ids.append(detected_cve)
            host = row.get('Host', row.get('asset.host_name', ''))
            if (not host):
                host = row.get('DNS Name', '')
            if (not host):
                host = row.get('IP Address', 'localhost')
            protocol = row.get('Protocol', row.get('protocol', ''))
            protocol = (protocol.lower() if protocol else None)
            port = str(row.get('Port', row.get('asset.port', '')))
            if (isinstance(port, str) and (port in {'', '0'})):
                port = None
            endpoint = (Endpoint.from_uri(host) if ('://' in host) else Endpoint(protocol=protocol, host=host, port=port))
            find.unsaved_endpoints.append(endpoint)
        return list(dupes.values())
