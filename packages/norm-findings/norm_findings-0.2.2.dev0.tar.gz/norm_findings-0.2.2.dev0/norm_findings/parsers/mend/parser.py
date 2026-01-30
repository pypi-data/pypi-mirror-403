# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import hashlib
import json
import logging
from contextlib import suppress
from datetime import datetime
from norm_findings.stubs.models import Finding
__author__ = 'dr3dd589 + testaccount90009 aka SH'
logger = logging.getLogger(__name__)

class MendParser():

    def get_scan_types(self):
        return ['Mend Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'Mend Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'Import JSON report'

    def get_findings(self, scan_file, test):
        if (scan_file is None):
            return []
        data = scan_file.read()
        try:
            content = json.loads(str(data, 'utf-8'))
        except Exception:
            content = json.loads(data)

        def _build_common_output(node, lib_name=None):
            cve = None
            component_name = None
            component_version = None
            impact = None
            ransomware_used = None
            known_exploited = None
            component_path = None
            kev_date = None
            description = 'No Description Available'
            cvss3_score = None
            mitigation = 'N/A'
            locations = []
            if ('component' in node):
                description = ((((((((((('**Vulnerability Description**: ' + node['vulnerability'].get('description', 'No Description Available')) + '\n\n') + '**Component Name**: ') + node['component'].get('name', '')) + '\n') + '**Component Type**: ') + node['component'].get('componentType', '')) + '\n') + '**Library Type**: ') + node['component'].get('libraryType', '')) + '\n')
                lib_name = node['component'].get('name')
                component_name = node['component'].get('artifactId')
                component_version = node['component'].get('version')
                impact = (('**Direct or Transitive Vulnerability**: ' + node['component'].get('dependencyType', '')) + '\n')
                cvss3_score = node['vulnerability'].get('score', None)
                kev_date_str = node['vulnerability'].get('publishDate', None)
                if kev_date_str:
                    with suppress(ValueError):
                        kev_date = datetime.strptime(kev_date_str, '%Y-%m-%dT%H:%M:%SZ').date()
                ransomware_used = node.get('malicious', None)
                known_exploited = node.get('exploitable', None)
                component_path = node['component'].get('path', None)
                fix_available = False
                if component_path:
                    locations.append(component_path)
                if ('topFix' in node):
                    try:
                        topfix_node = node.get('topFix')
                        mitigation = (((((('**Resolution**: ' + topfix_node.get('date', '')) + '\n') + topfix_node.get('message', '')) + '\n') + topfix_node.get('fixResolution', '')) + '\n')
                        fix_available = True
                    except Exception:
                        logger.exception('Error handling topFix node.')
            elif ('library' in node):
                node.get('project')
                description = (((((((((((((('**Description** : ' + node.get('description', '')) + '\n\n') + '**Library Name** : ') + node['library'].get('name', '')) + '\n\n') + '**Library Filename** : ') + node['library'].get('filename', '')) + '\n\n') + '**Library Description** : ') + node['library'].get('description', '')) + '\n\n') + '**Library Type** : ') + node['library'].get('type', '')) + '\n')
                lib_name = node['library'].get('filename')
                component_name = node['library'].get('artifactId')
                component_version = node['library'].get('version')
                cvss3_score = node.get('cvss3_score', None)
                fix_available = False
                if ('topFix' in node):
                    try:
                        topfix_node = node.get('topFix')
                        mitigation = '**Resolution** ({}): {}\n'.format(topfix_node.get('date'), topfix_node.get('fixResolution'))
                        fix_available = True
                    except Exception:
                        logger.exception('Error handling topFix node.')
            else:
                description = node.get('description', 'Unknown')
                fix_available = False
            cve = node.get('name')
            title = (('CVE-None | ' + lib_name) if (cve is None) else ((cve + ' | ') + lib_name))
            if ('cvss3_severity' in node):
                cvss_sev = node.get('cvss3_severity')
            elif ('vulnerability' in node):
                cvss_sev = node['vulnerability'].get('severity')
            else:
                cvss_sev = node.get('severity')
            severity = cvss_sev.lower().capitalize()
            cvss3_vector = node.get('scoreMetadataVector', None)
            severity_justification = 'CVSS v3 score: {} ({})'.format((cvss3_score if (cvss3_score is not None) else 'N/A'), (cvss3_vector if (cvss3_vector is not None) else 'N/A'))
            cwe = 1035
            filepaths = []
            if ('sourceFiles' in node):
                try:
                    sourceFiles_node = node.get('sourceFiles')
                    filepaths.extend((sfile.get('localPath') for sfile in sourceFiles_node))
                except Exception:
                    logger.exception('Error handling local paths for vulnerability.')
            if ('locations' in node):
                try:
                    locations_node = node.get('locations', [])
                    for location in locations_node:
                        path = location.get('path')
                        if (path is not None):
                            locations.append(path)
                except Exception:
                    logger.exception('Error handling local paths for vulnerability.')
            if locations:
                joined_locations = ', '.join(locations)
                if (len(joined_locations) > 3999):
                    total_length = 0
                    truncated_locations = []
                    for loc in locations:
                        loc_length = len(loc)
                        if (((total_length + loc_length) + len(truncated_locations)) <= 3996):
                            truncated_locations.append(loc)
                            total_length += loc_length
                        else:
                            break
                    locations = truncated_locations
                    locations.append('...')
            new_finding = Finding(title=title, test=test, description=description, severity=severity, cwe=cwe, mitigation=mitigation, file_path=', '.join(filepaths), component_name=component_name, component_version=component_version, severity_justification=severity_justification, dynamic_finding=True, cvssv3=cvss3_vector, cvssv3_score=(float(cvss3_score) if (cvss3_score is not None) else None), impact=(impact if (impact is not None) else None), steps_to_reproduce=(('**Locations Found**: ' + ', '.join(locations)) if (locations is not None) else None), kev_date=(kev_date if (kev_date is not None) else None), fix_available=fix_available)
            if (known_exploited is not None):
                new_finding.known_exploited = known_exploited
            if (ransomware_used is not None):
                new_finding.ransomware_used = ransomware_used
            if cve:
                new_finding.unsaved_vulnerability_ids = [cve]
            return new_finding
        findings = []
        if ('libraries' in content):
            tree_libs = content.get('libraries')
            for lib_node in tree_libs:
                if (('vulnerabilities' in lib_node) and (len(lib_node.get('vulnerabilities')) > 0)):
                    findings.extend((_build_common_output(vuln, lib_node.get('name')) for vuln in lib_node.get('vulnerabilities')))
        elif ('vulnerabilities' in content):
            tree_node = content['vulnerabilities']
            findings.extend((_build_common_output(node) for node in tree_node))
        elif ('components' in content):
            tree_components = content.get('components')
            for comp_node in tree_components:
                if (('response' in comp_node) and (len(comp_node.get('response')) > 0)):
                    findings.extend((_build_common_output(vuln, comp_node.get('name')) for vuln in comp_node.get('response')))
        elif ('response' in content):
            tree_node = content['response']
            if tree_node:
                findings.extend((_build_common_output(node) for node in tree_node if (node.get('findingInfo', {}).get('status') == 'ACTIVE')))

        def create_finding_key(f: Finding) -> str:
            return hashlib.md5((f.description.encode('utf-8') + f.title.encode('utf-8')), usedforsecurity=False).hexdigest()
        dupes = {}
        for finding in findings:
            dupe_key = create_finding_key(finding)
            if (dupe_key not in dupes):
                dupes[dupe_key] = finding
        return list(dupes.values())
