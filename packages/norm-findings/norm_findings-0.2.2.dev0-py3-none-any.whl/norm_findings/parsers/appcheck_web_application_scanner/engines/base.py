# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import re
from itertools import starmap
from typing import Any
import cvss.parser
import dateutil.parser
from cpe import CPE
from cvss.exceptions import CVSSError
from norm_findings.stubs.django.core.exceptions import ImproperlyConfigured
from norm_findings.stubs.models import Endpoint, Finding
MARKUP_STRIPPING_PATTERN = re.compile('\\[\\[markup\\]\\]|\\[\\[|\\]\\]')

def strip_markup(value: str) -> str:
    'Strips out "markup" from value'
    if value:
        return MARKUP_STRIPPING_PATTERN.sub('', value).strip()
    return value

def escape_non_printable(s: str) -> str:
    '\n    Replaces non-printable characters from a string, for some definition of non-printable that probably differs from the\n    uncountable other available definitions of non-printable, with a more-printable version.\n    '

    def escape_if_needed(x):
        if (x.isprintable() or (x in {'\r', '\n', '\t'})):
            return x
        return repr(x)[1:(- 1)]
    return ''.join([escape_if_needed(c) for c in s])

def cvss_score_to_severity(score: float, version: int) -> str:
    '\n    Maps a CVSS score with a given version to a severity level.\n    Mapping from https://nvd.nist.gov/vuln-metrics/cvss (modified slightly to have "Info" in range [0.0, 0.1) for CVSS\n        v3/v4)\n    '
    cvss_score = float(score)
    if (version == 2):
        if (cvss_score >= 7.0):
            severity = 'High'
        elif (cvss_score >= 4.0):
            severity = 'Medium'
        else:
            severity = 'Low'
    elif (cvss_score >= 9.0):
        severity = 'Critical'
    elif (cvss_score >= 7.0):
        severity = 'High'
    elif (cvss_score >= 4.0):
        severity = 'Medium'
    elif (cvss_score >= 0.1):
        severity = 'Low'
    else:
        severity = 'Info'
    return severity

class FieldType():
    '\n    Base class for attribute handlers for parsers. Callable, and calls the .handle() method, which should be implemented\n    by subclasses.\n\n    We lose type safety by accepting strings for target names; to try to work around this, the check() method on\n    subclasses should check whether the configuration for this object makes sense (or as much sense as can be determined\n    when the method is called) and raise an ImproperlyConfigured exception if it does not.\n    '

    def __init__(self, target_name):
        self.target_name = target_name

    def handle(self, engine_class, finding, value):
        pass

    def __call__(self, engine_class, finding, value):
        self.handle(engine_class, finding, value)

    def check(self, engine_parser):
        pass

class Attribute(FieldType):
    '\n    Class for a field that maps directly from one in the input data to a Finding attribute. Initialized with a Finding\n    attribute name, when called sets the value of that attribute to the passed-in value.\n    '

    def handle(self, engine_class, finding, value):
        setattr(finding, self.target_name, value)

    def check(self, engine_parser):
        if (not hasattr(Finding, self.target_name)):
            msg = f"Finding does not have attribute '{self.target_name}.'"
            raise ImproperlyConfigured(msg)

class DeMarkupedAttribute(Attribute):
    'Class for an Attribute (as above) but whose value is stripped of markup and non-printable chars prior to being set.'

    def handle(self, engine_class, finding, value):
        super().handle(engine_class, finding, escape_non_printable(strip_markup(value)))

class Method(FieldType):
    "\n    Class for a field that requires a method to process it. Initialized with a method name, when called it invokes the\n    method on the passed-in engine parser, passing in a Finding and value. It's expected that the method will update\n    the Finding as it sees fit (i.e., this class does not modify the Finding)\n    "

    def handle(self, engine_parser, finding, value):
        getattr(engine_parser, self.target_name)(finding, value)

    def check(self, engine_parser):
        if (not callable(getattr(engine_parser, self.target_name, None))):
            msg = f"{type(engine_parser).__name__} does not have method '{self.target_name}().'"
            raise ImproperlyConfigured(msg)

class BaseEngineParser():
    '\n    Parser for data shared by all engines used by AppCheck, as well as data from an unknown/unspecified engine.\n\n    Directly mapped attributes, from JSON object -> Finding attribute:\n        * _id -> unique_id_from_tool\n        * cvss_v3_vector -> cvssv3\n        * epss_base_score -> epss_score\n\n    Directly mapped attributes but value is stripped of "markup" first, JSON Object -> Finding attribute:\n        * title -> title\n        * description -> description\n        * solution -> mitigation\n\n    Data mapped with a bit of tinkering, JSON object -> Finding attribute:\n        * first_detected_at -> date (parse date)\n        * status -> active/false_p/risk_accepted (depending on value)\n        * cves -> unsaved_vulnerability_ids (vulnerability_ids)\n        * cpe -> component name/version\n        * notes -> appended to Finding description\n        * details -> appended to Finding description\n\n    Child classes can override the _ENGINE_FIELDS_MAP dictionary to support extended/different functionality as so\n    desired, without having to change/copy the common field parsing described above.\n    '
    SCANNING_ENGINE = 'Unknown'
    _COMMON_FIELDS_MAP: dict[(str, FieldType)] = {'_id': Attribute('unique_id_from_tool'), 'cvss_v3_vector': Attribute('cvssv3'), 'epss_base_score': Attribute('epss_score'), 'title': DeMarkupedAttribute('title'), 'description': DeMarkupedAttribute('description'), 'solution': DeMarkupedAttribute('mitigation'), 'first_detected_at': Method('parse_initial_date'), 'status': Method('parse_status'), 'cves': Method('parse_cves'), 'cpe': Method('parse_components'), 'notes': Method('parse_notes'), 'details': Method('parse_details')}
    _ENGINE_FIELDS_MAP: dict[(str, FieldType)] = {}

    def __init__(self):
        for field_handler in self.get_engine_fields().values():
            field_handler.check(self)

    def get_date(self, value: str) -> typing.Union[(str, None)]:
        try:
            return str(dateutil.parser.parse(value).date())
        except dateutil.parser.ParserError:
            return None

    def parse_initial_date(self, finding: Finding, value: str) -> None:
        finding.date = self.get_date(value)
    CVE_PATTERN = re.compile('CVE-[0-9]+-[0-9]+', re.IGNORECASE)

    def is_cve(self, c: str) -> bool:
        return bool((c and isinstance(c, str) and self.CVE_PATTERN.fullmatch(c)))

    def parse_cves(self, finding: Finding, value: list[str]) -> None:
        finding.unsaved_vulnerability_ids = [c.upper() for c in value if self.is_cve(c)]

    def parse_status(self, finding: Finding, value: str) -> None:
        value = value.lower()
        if (value == 'fixed'):
            finding.active = False
        elif (value == 'false_positive'):
            finding.false_p = True
        elif (value == 'acceptable_risk'):
            finding.risk_accepted = True

    def parse_cpe(self, cpe_str: str) -> (typing.Union[(str, None)], typing.Union[(str, None)]):
        if (not cpe_str):
            return (None, None)
        cpe_obj = CPE(cpe_str)
        return (((cpe_obj.get_product() and cpe_obj.get_product()[0]) or None), ((cpe_obj.get_version() and cpe_obj.get_version()[0]) or None))

    def parse_components(self, finding: Finding, value: list[str]) -> None:
        (finding.component_name, finding.component_version) = self.parse_cpe(value[0])

    def format_additional_description(self, section: str, value: str) -> str:
        return f'**{section}**: {escape_non_printable(strip_markup(value))}'

    def append_description(self, finding: Finding, addendum: dict[(str, str)]) -> None:
        if addendum:
            if finding.description:
                finding.description += '\n\n'
            finding.description += '\n\n'.join(list(starmap(self.format_additional_description, addendum.items())))

    def parse_notes(self, finding: Finding, value: str) -> None:
        self.append_description(finding, {'Notes': value})

    def extract_details(self, value: typing.Union[(str, dict[(str, (str | dict[(str, list[str])]))])]) -> dict[(str, str)]:
        if isinstance(value, dict):
            return {k: v for (k, v) in value.items() if (k != '_meta')}
        return {'Details': str(value)}

    def parse_details(self, finding: Finding, value: dict[(str, typing.Union[(str, dict[(str, list[str])])])]) -> None:
        self.append_description(finding, self.extract_details(value))

    def get_host(self, item: dict[(str, Any)]) -> str:
        return (item.get('url') or item.get('host') or item.get('ipv4_address') or None)

    def parse_port(self, item: Any) -> typing.Union[(int, None)]:
        try:
            int_val = int(item)
            if (0 < int_val <= 65535):
                return int_val
        except (ValueError, TypeError):
            pass
        return None

    def get_port(self, item: dict[(str, Any)]) -> typing.Union[(int, None)]:
        return self.parse_port(item.get('port'))

    def construct_endpoint(self, host: str, port: typing.Union[(int, None)]) -> Endpoint:
        endpoint = Endpoint.from_uri(host)
        if endpoint.host:
            if port:
                endpoint.port = port
        else:
            endpoint = Endpoint(host=host, port=port)
        return endpoint

    def parse_endpoints(self, item: dict[(str, Any)]) -> [Endpoint]:
        if (host := self.get_host(item)):
            port = self.get_port(item)
            return [self.construct_endpoint(host, port)]
        return []

    def set_endpoints(self, finding: Finding, item: Any) -> None:
        endpoints = self.parse_endpoints(item)
        finding.unsaved_endpoints.extend(endpoints)

    def parse_cvss_vector(self, value: str) -> typing.Union[(str, None)]:
        try:
            if ((severity := cvss.CVSS4(value).severity) in Finding.SEVERITIES):
                return severity
        except CVSSError:
            pass
        if (cvss_obj := cvss.parser.parse_cvss_from_text(value)):
            if ((severity := cvss_obj[0].severities()[0].title()) in Finding.SEVERITIES):
                return severity
        return None

    def set_severity(self, finding: Finding, item: Any) -> None:
        for (base_score_entry, cvss_version) in [('cvss_v4_base_score', 4), ('cvss_v3_base_score', 3), ('cvss_base_score', 2)]:
            if (base_score := item.get(base_score_entry)):
                finding.severity = cvss_score_to_severity(base_score, cvss_version)
                return
        for vector_type in ['cvss_v4_vector', 'cvss_v3_vector', 'cvss_vector']:
            if (vector := item.get(vector_type)):
                if (severity := self.parse_cvss_vector(vector)):
                    finding.severity = severity
                    return
        finding.severity = 'Info'

    def process_whole_item(self, finding: Finding, item: Any) -> None:
        self.set_severity(finding, item)
        self.set_endpoints(finding, item)

    def get_engine_fields(self) -> dict[(str, FieldType)]:
        return {**BaseEngineParser._COMMON_FIELDS_MAP, **self._ENGINE_FIELDS_MAP}

    def get_finding_key(self, finding: Finding) -> tuple:
        return (finding.severity, finding.title, tuple(sorted([(e.host, e.port) for e in finding.unsaved_endpoints])), self.SCANNING_ENGINE)

    def parse_finding(self, item: dict[(str, Any)]) -> tuple[(Finding, tuple)]:
        finding = Finding()
        for (field, field_handler) in self.get_engine_fields().items():
            if (value := item.get(field)):
                field_handler(self, finding, value)
        self.process_whole_item(finding, item)
        self.append_description(finding, {'Scanning Engine': self.SCANNING_ENGINE})
        return (finding, self.get_finding_key(finding))
