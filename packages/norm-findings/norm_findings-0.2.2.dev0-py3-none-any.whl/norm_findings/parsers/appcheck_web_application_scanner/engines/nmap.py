# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint

from typing import Any
from norm_findings.stubs.models import Endpoint
from norm_findings.parsers.appcheck_web_application_scanner.engines.base import BaseEngineParser

class NmapScanningEngineParser(BaseEngineParser):
    "\n    Parser for data from the Nmap scanning engine.\n\n    Nmap engine results include a list of ports in a 'port_table' data entry that we use to generate several endpoints\n    under the same Finding.\n    "
    SCANNING_ENGINE = 'NMapScanner'

    def is_port_table_entry(self, entry) -> bool:
        return ((len(entry) > 0) and self.parse_port(entry[0]))

    def get_ports(self, item) -> typing.Union[(list[int], list[None])]:
        meta = item.get('meta')
        if (not isinstance(meta, dict)):
            meta = {}
        if (ports := meta.get('port_table', [])):
            return [port for port_entry in ports if (port := self.is_port_table_entry(port_entry))]
        return [None]

    def parse_endpoints(self, item: dict[(str, Any)]) -> [Endpoint]:
        host = self.get_host(item)
        ports = self.get_ports(item)
        return [self.construct_endpoint(host, port) for port in ports]
