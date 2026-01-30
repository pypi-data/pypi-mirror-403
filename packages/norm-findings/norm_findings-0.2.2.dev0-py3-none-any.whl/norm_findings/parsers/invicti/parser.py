# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.netsparker.parser import NetsparkerParser

class InvictiParser(NetsparkerParser):

    def get_scan_types(self):
        return ['Invicti Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Invicti Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Invicti JSON format.'

    def get_findings(self, scan_file, test):
        '\n        Extended the NetSparker Parser since the Invicti is the a renamed version of Netsparker.\n\n        If there are deviations from the two report formats in the future, then this\n        function can be implemented then.\n        '
        return super().get_findings(scan_file, test)
