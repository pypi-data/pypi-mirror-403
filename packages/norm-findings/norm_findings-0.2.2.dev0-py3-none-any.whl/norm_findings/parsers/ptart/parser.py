# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import json
from norm_findings.parsers.parser_test import ParserTest
from norm_findings.parsers.ptart.assessment_parser import PTARTAssessmentParser
from norm_findings.parsers.ptart.retest_parser import PTARTRetestParser

class PTARTParser():
    '\n    Imports JSON reports from the PTART reporting tool\n    (https://github.com/certmichelin/PTART)\n    '

    def get_scan_types(self):
        return ['PTART Report']

    def get_label_for_scan_types(self, scan_type):
        return 'PTART Report'

    def get_description_for_scan_types(self, scan_type):
        return 'Import a PTART report file in JSON format.'

    def get_tests(self, scan_type, scan):
        data = json.load(scan)
        test = ParserTest(name='Pen Test Report', parser_type='Pen Test', version='')
        if ('name' in data):
            test.name = (data['name'] + ' Report')
            test.type = (data['name'] + ' Report')
        description = ptart_tools.generate_test_description_from_report(data)
        if description:
            test.description = description
        if ('start_date' in data):
            test.target_start = ptart_tools.parse_date(data['start_date'], '%Y-%m-%d')
        if ('end_date' in data):
            test.target_end = ptart_tools.parse_date(data['end_date'], '%Y-%m-%d')
        findings = self.get_items(data)
        test.findings = findings
        return [test]

    def get_findings(self, scan_file, test):
        data = json.load(scan_file)
        return self.get_items(data)

    def get_items(self, data):
        findings = PTARTAssessmentParser().get_test_data(data)
        findings.extend(PTARTRetestParser().get_test_data(data))
        return findings

    def requires_file(self, scan_type):
        return True
