# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.tenable.csv_format import TenableCSVParser
from norm_findings.parsers.tenable.xml_format import TenableXMLParser

class TenableParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Tenable CSV Parser\n\n        Fields:\n        - title: Made using the name, plugin name, and asset name from Tenable scanner.\n        - description: Made by combining synopsis and plugin output from Tenable Scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - mitigation: Set to solution from Tenable Scanner.\n        - impact: Set to definition description from Tenable Scanner.\n        - cvssv3: If present, set to cvssv3 from Tenable scanner.\n        - component_name: If present, set to product name from Tenable Scanner.\n        - component_version: If present, set to version from Tenable Scanner.\n\n        Return the list of fields used in the Tenable XML Parser\n\n        Fields:\n        - title: Set to plugin name from Tenable scanner.\n        - description: Made by combining synopsis element text and plugin output from Tenable Scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - mitigation: Set to solution from Tenable Scanner.\n        - impact: Made by combining description element text, cvss score, cvssv3 score, cvss vector, cvss base score, and cvss temporal score from Tenable Scanner.\n        - cwe: If present, set to cwe from Tenable scanner.\n        - cvssv3: If present, set to cvssv3 from Tenable scanner.\n        '
        return ['title', 'description', 'severity', 'mitigation', 'impact', 'cvssv3', 'component_name', 'component_version', 'cwe']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of dedupe fields used in the Tenable CSV Parser\n\n        Fields:\n        - title: Made using the name, plugin name, and asset name from Tenable scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - description: Made by combining synopsis and plugin output from Tenable Scanner.\n\n        NOTE: vulnerability_ids & cwe are not provided by parser\n\n        Return the list of dedupe fields used in the Tenable XML Parser\n\n        Fields:\n        - title: Made using the name, plugin name, and asset name from Tenable scanner.\n        - severity: Set to severity from Tenable Scanner converted to Defect Dojo format.\n        - cwe: If present, set to cwe from Tenable scanner.\n        - description: Made by combining synopsis and plugin output from Tenable Scanner.\n\n        NOTE: vulnerability_ids are not provided by parser\n        '
        return ['title', 'severity', 'description', 'cwe']

    def get_scan_types(self):
        return ['Tenable Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Tenable Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Reports can be imported as CSV or .nessus (XML) report formats.'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith(('.xml', '.nessus')):
            return TenableXMLParser().get_findings(scan_file, test)
        if scan_file.name.lower().endswith('.csv'):
            return TenableCSVParser().get_findings(scan_file, test)
        msg = 'Filename extension not recognized. Use .xml, .nessus or .csv'
        raise ValueError(msg)
