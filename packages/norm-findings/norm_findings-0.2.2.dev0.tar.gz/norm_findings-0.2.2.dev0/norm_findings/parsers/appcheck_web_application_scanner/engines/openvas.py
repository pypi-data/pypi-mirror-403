# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

from norm_findings.parsers.appcheck_web_application_scanner.engines.base import BaseEngineParser

class OpenVASScannerEngineParser(BaseEngineParser):
    '\n    Parser for data from the OpenVAS scanning engine.\n\n    Shares all functionality with BaseEngineParser, but registered under an explicit name.\n    '
    SCANNING_ENGINE = 'OpenVASScanner'
