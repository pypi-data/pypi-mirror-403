# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import json
from norm_findings.parsers.sonarqube.sonarqube_restapi_json import SonarQubeRESTAPIJSON

class SonarQubeRESTAPIZIP():

    def get_items(self, files, test, mode):
        total_findings_per_file = []
        for dictkey in files:
            if dictkey.endswith('.json'):
                json_content = json.loads(files[dictkey].decode('ascii'))
                total_findings_per_file += SonarQubeRESTAPIJSON().get_json_items(json_content, test, mode)
        return total_findings_per_file
