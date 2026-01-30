# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.aws_prowler_v3plus.prowler_v3 import AWSProwlerV3Parser
from norm_findings.parsers.aws_prowler_v3plus.prowler_v4 import AWSProwlerV4Parser

class AWSProwlerV3plusParser():
    SCAN_TYPE = ['AWS Prowler V3']

    def get_scan_types(self):
        return AWSProwlerV3plusParser.SCAN_TYPE

    def get_label_for_scan_types(self, scan_type):
        return AWSProwlerV3plusParser.SCAN_TYPE[0]

    def get_description_for_scan_types(self, scan_type):
        return 'Exports from AWS Prowler v3 in JSON format or from Prowler v4 in OCSF-JSON format.'

    def get_findings(self, scan_file, test):
        if scan_file.name.lower().endswith('.ocsf.json'):
            return AWSProwlerV4Parser().process_ocsf_json(scan_file, test)
        if scan_file.name.lower().endswith('.json'):
            return AWSProwlerV3Parser().process_json(scan_file, test)
        msg = 'Unknown file format'
        raise ValueError(msg)
