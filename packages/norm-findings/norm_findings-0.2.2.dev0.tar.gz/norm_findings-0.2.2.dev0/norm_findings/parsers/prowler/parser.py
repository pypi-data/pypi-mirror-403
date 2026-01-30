# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.prowler.parser_csv import ProwlerParserCSV
from norm_findings.parsers.prowler.parser_json import ProwlerParserJSON

class ProwlerParser():
    'Prowler is an Open Cloud Security that automates security and compliance in cloud environments. This parser is for Prowler JSON files and Prowler CSV files.'

    def get_scan_types(self):
        return ['Prowler Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Prowler Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Prowler report file can be imported in JSON format or in CSV format.'

    def get_findings(self, scan_file, test):
        name = getattr(scan_file, 'name', str(scan_file)).lower()
        if name.endswith('.csv'):
            return ProwlerParserCSV().get_findings(scan_file, test)
        if name.endswith('.json'):
            return ProwlerParserJSON().get_findings(scan_file, test)
        return []
