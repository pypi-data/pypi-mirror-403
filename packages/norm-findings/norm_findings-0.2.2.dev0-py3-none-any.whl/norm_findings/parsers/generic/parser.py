# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import json
from norm_findings.parsers.generic.csv_parser import GenericCSVParser
from norm_findings.parsers.generic.json_parser import GenericJSONParser
from norm_findings.parsers.parser_test import ParserTest

class GenericParser():
    ID = 'Generic Findings Import'

    def get_scan_types(self):
        return [self.ID]

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'Import Generic findings in CSV or JSON format.'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith('.csv'):
            return GenericCSVParser()._get_findings_csv(scan_file)
        if scan_file.name.lower().endswith('.json'):
            data = json.load(scan_file)
            test_internal = GenericJSONParser()._get_test_json(data)
            return test_internal.findings
        return GenericCSVParser()._get_findings_csv(scan_file)

    def get_tests(self, scan_type, filename):
        if filename.name.lower().endswith('.csv'):
            test = ParserTest(name=self.ID, parser_type=self.ID, version=None)
            test.findings = GenericCSVParser()._get_findings_csv(filename)
            return [test]
        data = json.load(filename)
        return [GenericJSONParser()._get_test_json(data)]

    def requires_file(self, scan_type):
        return True
