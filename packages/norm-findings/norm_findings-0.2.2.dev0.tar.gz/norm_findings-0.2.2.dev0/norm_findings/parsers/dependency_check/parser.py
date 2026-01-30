# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import datetime
import hashlib
import logging
import re
import dateutil
from cpe import CPE
from defusedxml import ElementTree
from packageurl import PackageURL
from norm_findings.stubs.models import Finding
from norm_findings.stubs.utils import parse_cvss_data
logger = logging.getLogger(__name__)

class DependencyCheckParser():
    SEVERITY_MAPPING = {'info': 'Info', 'low': 'Low', 'moderate': 'Medium', 'medium': 'Medium', 'high': 'High', 'critical': 'Critical'}
    CVSS_V3_MAPPINGS = {'attackVector': {'NETWORK': 'N', 'ADJACENT': 'A', 'LOCAL': 'L', 'PHYSICAL': 'P', 'N': 'N', 'A': 'A', 'L': 'L', 'P': 'P'}, 'attackComplexity': {'LOW': 'L', 'HIGH': 'H', 'L': 'L', 'H': 'H'}, 'privilegesRequired': {'NONE': 'N', 'LOW': 'L', 'HIGH': 'H', 'N': 'N', 'L': 'L', 'H': 'H'}, 'userInteraction': {'NONE': 'N', 'REQUIRED': 'R', 'N': 'N', 'R': 'R'}, 'scope': {'UNCHANGED': 'U', 'CHANGED': 'C', 'U': 'U', 'C': 'C'}, 'confidentialityImpact': {'NONE': 'N', 'LOW': 'L', 'HIGH': 'H', 'N': 'N', 'L': 'L', 'H': 'H'}, 'integrityImpact': {'NONE': 'N', 'LOW': 'L', 'HIGH': 'H', 'N': 'N', 'L': 'L', 'H': 'H'}, 'availabilityImpact': {'NONE': 'N', 'LOW': 'L', 'HIGH': 'H', 'N': 'N', 'L': 'L', 'H': 'H'}}

    def add_finding(self, finding, dupes):
        key_str = '|'.join([str(finding.title), str(finding.cwe), str(finding.file_path).lower()])
        key = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
        if (key not in dupes):
            dupes[key] = finding

    def get_filename_and_path_from_dependency(self, dependency, related_dependency, namespace):
        if (related_dependency is None):
            return (dependency.findtext(f'{namespace}fileName'), dependency.findtext(f'{namespace}filePath'))
        if related_dependency.findtext(f'{namespace}fileName'):
            return (related_dependency.findtext(f'{namespace}fileName'), related_dependency.findtext(f'{namespace}filePath'))
        return (None, None)

    def get_component_name_and_version_from_dependency(self, dependency, related_dependency, namespace):
        identifiers_node = dependency.find((namespace + 'identifiers'))
        if (identifiers_node is not None):
            package_node = identifiers_node.find((('.//' + namespace) + 'package'))
            if (package_node is not None):
                pck_id = package_node.findtext(f'{namespace}id')
                purl = PackageURL.from_string(pck_id)
                purl_parts = purl.to_dict()
                component_name = ((purl_parts['namespace'] + ':') if (purl_parts['namespace'] and (len(purl_parts['namespace']) > 0)) else '')
                component_name += (purl_parts['name'] if (purl_parts['name'] and (len(purl_parts['name']) > 0)) else '')
                component_name = (component_name or None)
                component_version = (purl_parts['version'] if (purl_parts['version'] and (len(purl_parts['version']) > 0)) else '')
                return (component_name, component_version)
            cpe_node = identifiers_node.find((('.//' + namespace) + 'identifier[@type="cpe"]'))
            if cpe_node:
                cpe_id = cpe_node.findtext(f'{namespace}name')
                cpe = CPE(cpe_id)
                component_name = ((cpe.get_vendor()[0] + ':') if (len(cpe.get_vendor()) > 0) else '')
                component_name += (cpe.get_product()[0] if (len(cpe.get_product()) > 0) else '')
                component_name = (component_name or None)
                component_version = (cpe.get_version()[0] if (len(cpe.get_version()) > 0) else None)
                return (component_name, component_version)
            maven_node = identifiers_node.find((('.//' + namespace) + 'identifier[@type="maven"]'))
            if (maven_node is not None):
                maven_parts = maven_node.findtext(f'{namespace}name').split(':')
                if (len(maven_parts) == 3):
                    component_name = ((maven_parts[0] + ':') + maven_parts[1])
                    component_version = maven_parts[2]
                    return (component_name, component_version)
        evidence_collected_node = dependency.find((namespace + 'evidenceCollected'))
        if (evidence_collected_node is not None):
            product_node = evidence_collected_node.find((('.//' + namespace) + 'evidence[@type="product"]'))
            if (product_node is not None):
                component_name = product_node.findtext(f'{namespace}value')
                version_node = evidence_collected_node.find((('.//' + namespace) + 'evidence[@type="version"]'))
                if (version_node is not None):
                    component_version = version_node.findtext(f'{namespace}value')
                return (component_name, component_version)
        return (None, None)

    def get_severity_and_cvss_meta(self, vulnerability, namespace) -> dict:
        severity = vulnerability.findtext(f'{namespace}severity')
        cvssv3 = None
        cvssv3_score = None
        if ((cvssv3_node := vulnerability.find((namespace + 'cvssV3'))) is not None):
            try:
                vector_parts = [f"AV:{self.CVSS_V3_MAPPINGS['attackVector'][cvssv3_node.findtext(f'{namespace}attackVector')]}", f"AC:{self.CVSS_V3_MAPPINGS['attackComplexity'][cvssv3_node.findtext(f'{namespace}attackComplexity')]}", f"PR:{self.CVSS_V3_MAPPINGS['privilegesRequired'][cvssv3_node.findtext(f'{namespace}privilegesRequired')]}", f"UI:{self.CVSS_V3_MAPPINGS['userInteraction'][cvssv3_node.findtext(f'{namespace}userInteraction')]}", f"S:{self.CVSS_V3_MAPPINGS['scope'][cvssv3_node.findtext(f'{namespace}scope')]}", f"C:{self.CVSS_V3_MAPPINGS['confidentialityImpact'][cvssv3_node.findtext(f'{namespace}confidentialityImpact')]}", f"I:{self.CVSS_V3_MAPPINGS['integrityImpact'][cvssv3_node.findtext(f'{namespace}integrityImpact')]}", f"A:{self.CVSS_V3_MAPPINGS['availabilityImpact'][cvssv3_node.findtext(f'{namespace}availabilityImpact')]}"]
                version = (cvssv3_node.findtext('version') or '3.1')
                vector = (f'CVSS:{version}/' + '/'.join(vector_parts))
                if (cvss_data := parse_cvss_data(vector)):
                    cvssv3 = cvss_data.get('cvssv3')
                    cvssv3_score = cvss_data.get('cvssv3_score')
                    severity = cvss_data.get('severity')
            except Exception as e:
                logger.debug(e)
        elif ((cvssv2_node := vulnerability.find((namespace + 'cvssV2'))) is not None):
            severity = cvssv2_node.findtext(f'{namespace}severity').lower().capitalize()
        if severity:
            if (severity.strip().lower() not in self.SEVERITY_MAPPING):
                logger.warning("Warning: Unknow severity value detected '%s'. Bypass to 'Medium' value", severity)
                severity = 'Medium'
            else:
                severity = self.SEVERITY_MAPPING[severity.strip().lower()]
        else:
            severity = 'Medium'
        return {'severity': severity, 'cvssv3': cvssv3, 'cvssv3_score': cvssv3_score}

    def get_finding_from_vulnerability(self, dependency, related_dependency, vulnerability, test, namespace):
        (dependency_filename, dependency_filepath) = self.get_filename_and_path_from_dependency(dependency, related_dependency, namespace)
        if (dependency_filename is None):
            return None
        tags = []
        mitigated = None
        is_Mitigated = False
        name = vulnerability.findtext(f'{namespace}name')
        if (vulnerability.find(f'{namespace}cwes') is not None):
            cwe_field = vulnerability.find(f'{namespace}cwes').findtext(f'{namespace}cwe')
        else:
            cwe_field = vulnerability.findtext(f'{namespace}cwe')
        description = vulnerability.findtext(f'{namespace}description')
        source = vulnerability.get('source')
        if source:
            description += ('\n**Source:** ' + str(source))
        notes = vulnerability.findtext(f'.//{namespace}notes')
        vulnerability_id = name[:28]
        if (vulnerability_id and (not vulnerability_id.startswith('CVE'))):
            vulnerability_id = None
        cwe = 1035
        if cwe_field:
            m = re.match('^(CWE-)?(\\d+)', cwe_field)
            if m:
                cwe = int(m.group(2))
        (component_name, component_version) = self.get_component_name_and_version_from_dependency(dependency, related_dependency, namespace)
        stripped_name = name
        stripped_name = re.sub('^CVE-\\d{4}-\\d{4,7}', '', stripped_name).strip()
        stripped_name = re.sub('^CWE-\\d+\\:', '', stripped_name).strip()
        stripped_name = re.sub('^CWE-\\d+', '', stripped_name).strip()
        if (component_name is None):
            logger.warning('component_name was None for File: %s, using dependency file name instead.', dependency_filename)
            component_name = dependency_filename
        reference_detail = None
        references_node = vulnerability.find((namespace + 'references'))
        if (references_node is not None):
            reference_detail = ''
            for reference_node in references_node.findall((namespace + 'reference')):
                ref_source = reference_node.findtext(f'{namespace}source')
                ref_url = reference_node.findtext(f'{namespace}url')
                ref_name = reference_node.findtext(f'{namespace}name')
                if (ref_url == ref_name):
                    reference_detail += f'''**Source:** {ref_source}
**URL:** {ref_url}

'''
                else:
                    reference_detail += f'''**Source:** {ref_source}
**URL:** {ref_url}
**Name:** {ref_name}

'''
        if (related_dependency is not None):
            tags.append('related')
        if (vulnerability.tag == f'{namespace}suppressedVulnerability'):
            if (notes is None):
                notes = 'Document on why we are suppressing this vulnerability is missing!'
                tags.append('no_suppression_document')
            mitigation = f'''**This vulnerability is mitigated and/or suppressed:** {notes}
'''
            mitigation += f'Update {component_name}:{component_version} to at least the version recommended in the description'
            mitigated = datetime.datetime.now(datetime.timezone.utc)
            is_Mitigated = True
            active = False
            tags.append('suppressed')
        else:
            mitigation = f'Update {component_name}:{component_version} to at least the version recommended in the description'
            description += ('\n**Filepath:** ' + str(dependency_filepath))
            active = True
        finding = Finding(title=f'{component_name}:{component_version} | {name}', file_path=dependency_filename, test=test, cwe=cwe, description=description, mitigation=mitigation, mitigated=mitigated, is_mitigated=is_Mitigated, tags=tags, active=active, dynamic_finding=False, static_finding=True, references=reference_detail, component_name=component_name, component_version=component_version, **self.get_severity_and_cvss_meta(vulnerability, namespace))
        if vulnerability_id:
            finding.unsaved_vulnerability_ids = [vulnerability_id]
        return finding

    def get_scan_types(self):
        return ['Dependency Check Scan']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'OWASP Dependency Check output can be imported in Xml format.'

    def get_findings(self, scan_file, test):
        dupes = {}
        namespace = ''
        content = scan_file.read()
        scan = ElementTree.fromstring(content)
        regex = '{.*}'
        matches = re.match(regex, scan.tag)
        try:
            namespace = matches.group(0)
        except BaseException:
            namespace = ''
        dependencies = scan.find((namespace + 'dependencies'))
        scan_date = None
        if (scan.find(f'{namespace}projectInfo') is not None):
            projectInfo_node = scan.find(f'{namespace}projectInfo')
            if projectInfo_node.findtext(f'{namespace}reportDate'):
                scan_date = dateutil.parser.parse(projectInfo_node.findtext(f'{namespace}reportDate'))
        if (dependencies is not None):
            for dependency in dependencies.findall((namespace + 'dependency')):
                vulnerabilities = dependency.find((namespace + 'vulnerabilities'))
                if (vulnerabilities is not None):
                    for vulnerability in vulnerabilities.findall((namespace + 'vulnerability')):
                        if (vulnerability is not None):
                            finding = self.get_finding_from_vulnerability(dependency, None, vulnerability, test, namespace)
                            if scan_date:
                                finding.date = scan_date
                            self.add_finding(finding, dupes)
                            relatedDependencies = dependency.find((namespace + 'relatedDependencies'))
                            if (relatedDependencies is not None):
                                for relatedDependency in relatedDependencies.findall((namespace + 'relatedDependency')):
                                    finding = self.get_finding_from_vulnerability(dependency, relatedDependency, vulnerability, test, namespace)
                                    if finding:
                                        if scan_date:
                                            finding.date = scan_date
                                        self.add_finding(finding, dupes)
                    for suppressedVulnerability in vulnerabilities.findall((namespace + 'suppressedVulnerability')):
                        if (suppressedVulnerability is not None):
                            finding = self.get_finding_from_vulnerability(dependency, None, suppressedVulnerability, test, namespace)
                            if scan_date:
                                finding.date = scan_date
                            self.add_finding(finding, dupes)
        return list(dupes.values())
