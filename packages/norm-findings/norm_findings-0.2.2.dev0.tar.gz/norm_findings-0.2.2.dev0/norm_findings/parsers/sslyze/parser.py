# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from .parser_json import SSLyzeJSONParser
from .parser_xml import SSLyzeXMLParser

class SslyzeParser():
    'SSLyze support JSON and XML'

    def get_scan_types(self):
        return ['SSLyze Scan (JSON)', 'Sslyze Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        if (scan_type == 'SSLyze Scan (JSON)'):
            return 'Import JSON report of SSLyze version 3 and higher.'
        return 'Import XML report of SSLyze version 2 scan.'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return []
        if scan_file.name.lower().endswith('.xml'):
            return SSLyzeXMLParser().get_findings(scan_file, test)
        if scan_file.name.lower().endswith('.json'):
            return SSLyzeJSONParser().get_findings(scan_file, test)
        msg = 'Unknown File Format'
        raise ValueError(msg)
