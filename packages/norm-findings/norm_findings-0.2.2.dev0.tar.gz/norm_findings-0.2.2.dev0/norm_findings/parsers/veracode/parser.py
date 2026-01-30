# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.veracode.json_parser import VeracodeJSONParser
from norm_findings.parsers.veracode.xml_parser import VeracodeXMLParser

class VeracodeParser():

    def get_scan_types(self):
        return ['Veracode Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Veracode Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Reports can be imported as JSON or XML report formats.'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith('.xml'):
            return VeracodeXMLParser().get_findings(scan_file, test)
        if scan_file.name.lower().endswith('.json'):
            return VeracodeJSONParser().get_findings(scan_file, test)
        msg = 'Filename extension not recognized. Use .xml or .json'
        raise ValueError(msg)
