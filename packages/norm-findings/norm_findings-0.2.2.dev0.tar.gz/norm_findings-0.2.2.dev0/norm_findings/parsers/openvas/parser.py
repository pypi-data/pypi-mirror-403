# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.openvas.parser_v1.csv_parser import OpenVASCSVParser
from norm_findings.parsers.openvas.parser_v1.xml_parser import OpenVASXMLParser
from norm_findings.parsers.openvas.parser_v2.csv_parser import get_findings_from_csv
from norm_findings.parsers.openvas.parser_v2.xml_parser import get_findings_from_xml

class OpenVASParser():

    def get_scan_types(self):
        return ['OpenVAS Parser']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import CSV or XML output of Greenbone OpenVAS report.'

    def get_findings(self, scan_file, test):
        if str(scan_file.name).endswith('.csv'):
            return OpenVASCSVParser().get_findings(scan_file, test)
        if str(scan_file.name).endswith('.xml'):
            return OpenVASXMLParser().get_findings(scan_file, test)
        return None

class OpenVASParserV2():

    def get_scan_types(self):
        return ['OpenVAS Parser v2']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import CSV or XML output of Greenbone OpenVAS report.'

    def get_findings(self, scan_file, test):
        if str(scan_file.name).endswith('.csv'):
            return get_findings_from_csv(scan_file, test)
        if str(scan_file.name).endswith('.xml'):
            return get_findings_from_xml(scan_file, test)
        return None
