# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.cyclonedx.json_parser import CycloneDXJSONParser
from norm_findings.parsers.cyclonedx.xml_parser import CycloneDXXMLParser

class CycloneDXParser():
    '\n    CycloneDX is a lightweight software bill of materials (SBOM) standard designed for use in application security\n    contexts and supply chain component analysis.\n    https://www.cyclonedx.org/\n    '

    def get_scan_types(self):
        return ['CycloneDX Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'CycloneDX Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Support CycloneDX XML and JSON report formats (compatible with 1.4).'

    def get_findings(self, scan_file, test):
        if scan_file.name.strip().lower().endswith('.json'):
            return CycloneDXJSONParser()._get_findings_json(scan_file, test)
        return CycloneDXXMLParser()._get_findings_xml(scan_file, test)
