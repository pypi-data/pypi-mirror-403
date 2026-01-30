# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import re
from norm_findings.stubs.models import Finding
from norm_findings.parsers.appcheck_web_application_scanner.engines.base import BaseEngineParser

class AppCheckScanningEngineParser(BaseEngineParser):
    "\n    Parser for data from the (proprietary?) AppCheck scanning engine.\n\n    Results from this engine may include request/response data nested in the 'details' entry. This extracts those values\n    and stores them in the Finding unsaved_request/unsaved_response attributes.\n    "
    SCANNING_ENGINE = 'NewAppCheckScannerMultiple'
    HTTP_1_REQUEST_RESPONSE_PATTERN = re.compile('^--->\\n\\n(.+)\\n\\n<---\\n\\n(.+)$', re.DOTALL)
    HTTP_2_REQUEST_RESPONSE_PATTERN = re.compile('^HTTP/2 Request Headers:\\n\\n(.+)\\r\\nHTTP/2 Response Headers:\\n\\n(.+)$', re.DOTALL)

    def extract_request_response(self, finding: Finding, value: dict[(str, [str])]) -> None:
        if (messages := value.get('Messages')):
            if (rr_details := (self.HTTP_1_REQUEST_RESPONSE_PATTERN.findall(messages) or self.HTTP_2_REQUEST_RESPONSE_PATTERN.findall(messages))):
                value.pop('Messages')
                (finding.unsaved_request, finding.unsaved_response) = (d.strip() for d in rr_details[0])

    def parse_details(self, finding: Finding, value: dict[(str, typing.Union[(str, dict[(str, list[str])])])]) -> None:
        self.extract_request_response(finding, value)
        return super().parse_details(finding, value)
