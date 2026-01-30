# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.fortify.fpr_parser import FortifyFPRParser
from norm_findings.parsers.fortify.xml_parser import FortifyXMLParser

class FortifyParser():

    def get_scan_types(self):
        return ['Fortify Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Findings in FPR or XML file format.'

    def get_findings(self, scan_file, test):
        if str(scan_file.name).endswith('.xml'):
            return FortifyXMLParser().parse_xml(scan_file, test)
        if str(scan_file.name).endswith('.fpr'):
            return FortifyFPRParser().parse_fpr(scan_file, test)
        msg = 'Filename extension not recognized. Use .xml or .fpr'
        raise ValueError(msg)
