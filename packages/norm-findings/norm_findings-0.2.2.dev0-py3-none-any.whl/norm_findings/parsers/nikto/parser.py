# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.nikto.json_parser import NiktoJSONParser
from norm_findings.parsers.nikto.xml_parser import NiktoXMLParser

class NiktoParser():
    '\n    Nikto web server scanner - https://cirt.net/Nikto2\n\n    The current parser support 3 sources:\n     - XML output (old)\n     - new XML output (with nxvmlversion="1.2" type)\n     - JSON output\n\n    See: https://github.com/sullo/nikto\n    '

    def get_scan_types(self):
        return ['Nikto Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'XML output (old and new nxvmlversion="1.2" type) or JSON output'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith('.xml'):
            return NiktoXMLParser().process_xml(scan_file, test)
        if scan_file.name.lower().endswith('.json'):
            return NiktoJSONParser().process_json(scan_file, test)
        msg = 'Unknown File Format'
        raise ValueError(msg)
