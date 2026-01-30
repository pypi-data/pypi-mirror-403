# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
import logging
from norm_findings.stubs.models import Finding
logger = logging.getLogger(__name__)

class DependencyTrackParser():
    '\n    A class that can be used to parse the JSON Finding Packaging Format (FPF) export from OWASP Dependency Track.\n\n    See here for more info on this JSON format: https://docs.dependencytrack.org/integrations/file-formats/\n\n    A typical Finding Packaging Format (FPF) export looks like the following:\n\n    {\n        "version": "1.0",\n        "meta" : {\n            "application": "Dependency-Track",\n            "version": "3.4.0",\n            "timestamp": "2018-11-18T23:31:42Z",\n            "baseUrl": "http://dtrack.example.org"\n        },\n        "project" : {\n            "uuid": "ca4f2da9-0fad-4a13-92d7-f627f3168a56",\n            "name": "Acme Example",\n            "version": "1.0",\n            "description": "A sample application"\n        },\n        "findings" : [\n            {\n                "component": {\n                    "uuid": "b815b581-fec1-4374-a871-68862a8f8d52",\n                    "name": "timespan",\n                    "version": "2.3.0",\n                    "purl": "pkg:npm/timespan@2.3.0"\n                },\n                "vulnerability": {\n                    "uuid": "115b80bb-46c4-41d1-9f10-8a175d4abb46",\n                    "source": "NPM",\n                    "vulnId": "533",\n                    "title": "Regular Expression Denial of Service",\n                    "subtitle": "timespan",\n                    "severity": "LOW",\n                    "severityRank": 3,\n                    "cweId": 400,\n                    "cweName": "Uncontrolled Resource Consumption (\'Resource Exhaustion\')",\n                    "description": "Affected versions of `timespan`...",\n                    "recommendation": "No direct patch is available..."\n                },\n                "analysis": {\n                    "state": "NOT_SET",\n                    "isSuppressed": false\n                },\n                "matrix": "ca4f2da9-0fad-4a13-92d7-f627f3168a56:b815b581-fec1-4374-a871-68862a8f8d52:115b80bb-46c4-41d1-9f10-8a175d4abb46"\n            },\n            {\n                "component": {\n                    "uuid": "979f87f5-eaf5-4095-9d38-cde17bf9228e",\n                    "name": "uglify-js",\n                    "version": "2.4.24",\n                    "purl": "pkg:npm/uglify-js@2.4.24"\n                },\n                "vulnerability": {\n                    "uuid": "701a3953-666b-4b7a-96ca-e1e6a3e1def3",\n                    "source": "NPM",\n                    "vulnId": "48",\n                    "title": "Regular Expression Denial of Service",\n                    "subtitle": "uglify-js",\n                    "severity": "LOW",\n                    "severityRank": 3,\n                    "cweId": 400,\n                    "cweName": "Uncontrolled Resource Consumption (\'Resource Exhaustion\')",\n                    "description": "Versions of `uglify-js` prior to...",\n                    "recommendation": "Update to version 2.6.0 or later."\n                },\n                "analysis": {\n                    "isSuppressed": false\n                },\n                "matrix": "ca4f2da9-0fad-4a13-92d7-f627f3168a56:979f87f5-eaf5-4095-9d38-cde17bf9228e:701a3953-666b-4b7a-96ca-e1e6a3e1def3"\n            }]\n    }\n    '

    def _convert_dependency_track_severity_to_dojo_severity(self, dependency_track_severity):
        '\n        Converts a Dependency Track severity to a DefectDojo severity.\n        :param dependency_track_severity: The severity from Dependency Track\n        :return: A DefectDojo severity if a mapping can be found; otherwise a null value is returned\n        '
        severity = dependency_track_severity.lower()
        if (severity == 'critical'):
            return 'Critical'
        if (severity == 'high'):
            return 'High'
        if (severity == 'medium'):
            return 'Medium'
        if (severity == 'low'):
            return 'Low'
        if severity.startswith('info'):
            return 'Informational'
        return None

    def _convert_dependency_track_finding_to_dojo_finding(self, dependency_track_finding, test):
        '\n        Converts a Dependency Track finding to a DefectDojo finding\n\n        :param dependency_track_finding: A dictionary representing a single finding from a Dependency Track Finding Packaging Format (FPF) export\n        :param test: The test that the DefectDojo finding should be associated to\n        :return: A DefectDojo Finding model\n        '
        if ('vulnerability' not in dependency_track_finding):
            msg = "Missing 'vulnerability' node from finding!"
            raise ValueError(msg)
        if ('vulnId' not in dependency_track_finding['vulnerability']):
            msg = "Missing 'vulnId' node from vulnerability!"
            raise ValueError(msg)
        vuln_id = dependency_track_finding['vulnerability']['vulnId']
        if ('source' not in dependency_track_finding['vulnerability']):
            msg = "Missing 'source' node from vulnerability!"
            raise ValueError(msg)
        source = dependency_track_finding['vulnerability']['source']
        if ('component' not in dependency_track_finding):
            msg = "Missing 'component' node from finding!"
            raise ValueError(msg)
        if ('name' not in dependency_track_finding['component']):
            msg = "Missing 'name' node from component!"
            raise ValueError(msg)
        component_name = dependency_track_finding['component']['name']
        if (('version' in dependency_track_finding['component']) and (dependency_track_finding['component']['version'] is not None)):
            component_version = dependency_track_finding['component']['version']
        else:
            component_version = None
        version_description = (component_version if (component_version is not None) else '')
        title = f'{component_name}:{version_description} affected by: {vuln_id} ({source})'
        if dependency_track_finding['vulnerability'].get('aliases'):
            set_of_ids = set()
            set_of_sources = {'cveId', 'sonatypeId', 'ghsaId', 'osvId', 'snykId', 'gsdId', 'vulnDbId'}
            for alias in dependency_track_finding['vulnerability']['aliases']:
                for source in set_of_sources:
                    if (source in alias):
                        set_of_ids.add(alias[source])
            vulnerability_id = list(set_of_ids)
        else:
            vulnerability_id = ([vuln_id] if ((source is not None) and (source.upper() == 'NVD')) else None)
        if (('cweId' in dependency_track_finding['vulnerability']) and (dependency_track_finding['vulnerability']['cweId'] is not None)):
            cwe = dependency_track_finding['vulnerability']['cweId']
        else:
            cwe = 1035
        if (component_version is not None):
            component_description = f'Version {component_version} of the {component_name} component'
        else:
            component_description = f'The {component_name} component'
        vulnerability_description = f'You are using a component with a known vulnerability. {component_description} is affected by the vulnerability with an id of {vuln_id} as identified by {source}.'
        if (('purl' in dependency_track_finding['component']) and (dependency_track_finding['component']['purl'] is not None)):
            component_purl = dependency_track_finding['component']['purl']
            vulnerability_description += f'''
The purl of the affected component is: {component_purl}.'''
            file_path = component_purl
        else:
            file_path = 'unknown'
        if (('title' in dependency_track_finding['vulnerability']) and (dependency_track_finding['vulnerability']['title'] is not None)):
            vulnerability_description += '\nVulnerability Title: {title}'.format(title=dependency_track_finding['vulnerability']['title'])
        if (('subtitle' in dependency_track_finding['vulnerability']) and (dependency_track_finding['vulnerability']['subtitle'] is not None)):
            vulnerability_description += '\nVulnerability Subtitle: {subtitle}'.format(subtitle=dependency_track_finding['vulnerability']['subtitle'])
        if (('description' in dependency_track_finding['vulnerability']) and (dependency_track_finding['vulnerability']['description'] is not None)):
            vulnerability_description += '\nVulnerability Description: {description}'.format(description=dependency_track_finding['vulnerability']['description'])
        if (('uuid' in dependency_track_finding['vulnerability']) and (dependency_track_finding['vulnerability']['uuid'] is not None)):
            vuln_id_from_tool = dependency_track_finding['vulnerability']['uuid']
        dependency_track_severity = dependency_track_finding['vulnerability']['severity']
        vulnerability_severity = self._convert_dependency_track_severity_to_dojo_severity(dependency_track_severity)
        if (vulnerability_severity is None):
            logger.warning('Detected severity of %s that could not be mapped for %s. Defaulting to Informational!', dependency_track_severity, title)
            vulnerability_severity = 'Informational'
        cvss_score = dependency_track_finding['vulnerability'].get('cvssV3BaseScore')
        analysis = dependency_track_finding.get('analysis')
        is_false_positive = bool(((analysis is not None) and (analysis.get('state') == 'FALSE_POSITIVE')))
        epss_percentile = dependency_track_finding['vulnerability'].get('epssPercentile', None)
        epss_score = dependency_track_finding['vulnerability'].get('epssScore', None)
        finding = Finding(title=title, test=test, cwe=cwe, description=vulnerability_description, severity=vulnerability_severity, false_p=is_false_positive, component_name=component_name, component_version=component_version, file_path=file_path, vuln_id_from_tool=vuln_id_from_tool, static_finding=True, dynamic_finding=False)
        if is_false_positive:
            finding.is_mitigated = True
            finding.active = False
        if vulnerability_id:
            finding.unsaved_vulnerability_ids = vulnerability_id
        if cvss_score:
            finding.cvssv3_score = cvss_score
        if epss_score:
            finding.epss_score = epss_score
        if epss_percentile:
            finding.epss_percentile = epss_percentile
        return finding

    def get_scan_types(self):
        return ['Dependency Track Finding Packaging Format (FPF) Export']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'The Finding Packaging Format (FPF) from OWASP Dependency Track can be imported in JSON format. See here for more info on this JSON format.'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return []
        data = scan_file.read()
        try:
            findings_export_dict = json.loads(str(data, 'utf-8'))
        except:
            findings_export_dict = json.loads(data)
        if (len(findings_export_dict.keys()) == 0):
            return []
        if (('findings' not in findings_export_dict) or (not findings_export_dict['findings'])):
            return []
        items = []
        for dependency_track_finding in findings_export_dict['findings']:
            dojo_finding = self._convert_dependency_track_finding_to_dojo_finding(dependency_track_finding, test)
            items.append(dojo_finding)
        return items
