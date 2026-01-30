# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.acunetix.parse_acunetix360_json import AcunetixJSONParser
from norm_findings.parsers.acunetix.parse_acunetix_xml import AcunetixXMLParser

class AcunetixParser():
    'Parser for Acunetix XML files and Acunetix 360 JSON files.'

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Acunetix XML Parser.\n\n        Fields:\n        - title: Set to the name outputted by the Acunetix XML Scanner.\n        - severity: Set to severity from Acunetix XML Scanner converted into Defect Dojo format.\n        - description: Set to description, Details, and TechnivalDetails variables outputted from Acunetix XML Scanner.\n        - false_p: Set to True/False based on Defect Dojo standards.\n        - static_finding: Set to True by default and updated to False if requests are present.\n        - dynamic_finding: Set to False by default and updated to True if requests are present.\n        - nb_occurences: Set to 1 and increased based on presence of occurences.\n        - impact: Set to impact outputted from Acunetix XML Scanner if it is present.\n        - mitigation: Set to Recommendation outputted from Acunetix XML Scanner if it is present.\n        - date: Set to StartTime outputted from Acunetix XML Scanner if it is present.\n        - cwe: Set to converted cwe outputted from Acunetix XML Scanner if it is present.\n        - cvssv3: Set to converted cvssv3 values outputted from Acunetix XML Scanner if it is present.\n\n        Return the list of fields used in the Acunetix 360 Parser.\n\n        Fields:\n        - title: Set to the name outputted by the Acunetix 360 Scanner.\n        - description: Set to Description variable outputted from Acunetix 360 Scanner.\n        - severity: Set to severity from Acunetix 360 Scanner converted into Defect Dojo format.\n        - mitigation: Set to RemedialProcedure variable outputted from Acunetix 360 Scanner if it is present.\n        - impact: Set to Impact variable outputted from Acunetix 360 Scanner if it is present.\n        - date: Set to FirstSeenDate variable outputted from Acunetix 360 Scanner if present. If not, it is set to Generated variable from output.\n        - cwe: Set to converted cwe in Classification variable outputted from Acunetix 360 Scanner if it is present.\n        - static_finding: Set to True.\n        - cvssv3: Set to converted cvssv3 in Classification variable outputted from Acunetix 360 Scanner if it is present.\n        - risk_accepted: Set to True if AcceptedRisk is present in State variable outputted from Acunetix 360 Scanner. No value if variable is not present.\n        - active: Set to false.\n        '
        return ['title', 'severity', 'description', 'false_p', 'static_finding', 'dynamic_finding', 'nb_occurences', 'impact', 'mitigation', 'date', 'cwe', 'cvssv3', 'risk_accepted', 'active']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Acunetix XML Parser.\n\n        Fields:\n        - title: Set to the name outputted by the Acunetix XML Scanner.\n        - description: Set to description, Details, and TechnivalDetails variables outputted from Acunetix XML Scanner.\n\n        Return the list of fields used for deduplication in the Acunetix 360 Parser.\n\n        Fields:\n        - title: Set to the name outputted by the Acunetix 360 Scanner.\n        - description: Set to Description variable outputted from Acunetix 360 Scanner.\n        '
        return ['title', 'description']

    def get_scan_types(self):
        return ['Acunetix Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Acunetix Scanner'

    def get_description_for_scan_types(self, scan_type):
        return 'Acunetix Scanner in XML format or Acunetix 360 Scanner in JSON format'

    def get_findings(self, scan_file, test):
        if ('.xml' in str(scan_file)):
            return AcunetixXMLParser().get_findings(scan_file, test)
        if ('.json' in str(scan_file)):
            return AcunetixJSONParser().get_findings(scan_file, test)
        return None
