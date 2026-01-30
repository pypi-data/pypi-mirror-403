# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from norm_findings.stubs.models import Finding

class WizcliParsers():

    @staticmethod
    def parse_libraries(libraries, test):
        findings = []
        if libraries:
            for library in libraries:
                lib_name = library.get('name', 'N/A')
                lib_version = library.get('version', 'N/A')
                lib_path = library.get('path', 'N/A')
                vulnerabilities = library.get('vulnerabilities', [])
                for vulnerability in vulnerabilities:
                    vuln_name = vulnerability.get('name', 'N/A')
                    severity = vulnerability.get('severity', 'low').lower().capitalize()
                    fixed_version = vulnerability.get('fixedVersion', 'N/A')
                    source = vulnerability.get('source', 'N/A')
                    description = vulnerability.get('description', 'N/A')
                    score = vulnerability.get('score', 'N/A')
                    exploitability_score = vulnerability.get('exploitabilityScore', 'N/A')
                    has_exploit = vulnerability.get('hasExploit', False)
                    has_cisa_kev_exploit = vulnerability.get('hasCisaKevExploit', False)
                    finding_description = f'''**Library Name**: {lib_name}
**Library Version**: {lib_version}
**Library Path**: {lib_path}
**Vulnerability Name**: {vuln_name}
**Fixed Version**: {fixed_version}
**Source**: {source}
**Description**: {description}
**Score**: {score}
**Exploitability Score**: {exploitability_score}
**Has Exploit**: {has_exploit}
**Has CISA KEV Exploit**: {has_cisa_kev_exploit}
'''
                    finding = Finding(title=f'{lib_name} - {vuln_name}', description=finding_description, file_path=lib_path, severity=severity, static_finding=True, dynamic_finding=False, mitigation=None, test=test)
                    findings.append(finding)
        return findings

    @staticmethod
    def parse_secrets(secrets, test):
        findings = []
        if secrets:
            for secret in secrets:
                secret_id = secret.get('id', 'N/A')
                desc = secret.get('description', 'N/A')
                severity = 'High'
                file_name = secret.get('path', 'N/A')
                line_number = secret.get('lineNumber', 'N/A')
                match_content = secret.get('type', 'N/A')
                description = f'''**Secret ID**: {secret_id}
**Description**: {desc}
**File Name**: {file_name}
**Line Number**: {line_number}
**Match Content**: {match_content}
'''
                finding = Finding(title=f'Secret: {desc}', description=description, severity=severity, file_path=file_name, line=line_number, static_finding=True, dynamic_finding=False, mitigation=None, test=test)
                findings.append(finding)
        return findings

    @staticmethod
    def parse_rule_matches(rule_matches, test):
        findings = []
        if rule_matches:
            for rule_match in rule_matches:
                rule = rule_match.get('rule', {})
                rule_id = rule.get('id', 'N/A')
                rule_name = rule.get('name', 'N/A')
                severity = rule_match.get('severity', 'low').lower().capitalize()
                matches = rule_match.get('matches', [])
                if matches:
                    for match in matches:
                        resource_name = match.get('resourceName', 'N/A')
                        file_name = match.get('fileName', 'N/A')
                        line_number = match.get('lineNumber', 'N/A')
                        match_content = match.get('matchContent', 'N/A')
                        expected = match.get('expected', 'N/A')
                        found = match.get('found', 'N/A')
                        file_type = match.get('fileType', 'N/A')
                        description = f'''**Rule ID**: {rule_id}
**Rule Name**: {rule_name}
**Resource Name**: {resource_name}
**File Name**: {file_name}
**Line Number**: {line_number}
**Match Content**: {match_content}
**Expected**: {expected}
**Found**: {found}
**File Type**: {file_type}
'''
                        finding = Finding(title=f'{rule_name} - {resource_name}', description=description, severity=severity, file_path=file_name, line=line_number, static_finding=True, dynamic_finding=False, mitigation=None, test=test)
                        findings.append(finding)
        return findings

    @staticmethod
    def parse_os_packages(os_packages, test):
        findings = []
        if os_packages:
            for osPackage in os_packages:
                pkg_name = osPackage.get('name', 'N/A')
                pkg_version = osPackage.get('version', 'N/A')
                vulnerabilities = osPackage.get('vulnerabilities', [])
                for vulnerability in vulnerabilities:
                    vuln_name = vulnerability.get('name', 'N/A')
                    severity = vulnerability.get('severity', 'low').lower().capitalize()
                    fixed_version = vulnerability.get('fixedVersion', 'N/A')
                    source = vulnerability.get('source', 'N/A')
                    description = vulnerability.get('description', 'N/A')
                    score = vulnerability.get('score', 'N/A')
                    exploitability_score = vulnerability.get('exploitabilityScore', 'N/A')
                    has_exploit = vulnerability.get('hasExploit', False)
                    has_cisa_kev_exploit = vulnerability.get('hasCisaKevExploit', False)
                    finding_description = f'''**OS Package Name**: {pkg_name}
**OS Package Version**: {pkg_version}
**Vulnerability Name**: {vuln_name}
**Fixed Version**: {fixed_version}
**Source**: {source}
**Description**: {description}
**Score**: {score}
**Exploitability Score**: {exploitability_score}
**Has Exploit**: {has_exploit}
**Has CISA KEV Exploit**: {has_cisa_kev_exploit}
'''
                    finding = Finding(title=f'{pkg_name} - {vuln_name}', description=finding_description, severity=severity, static_finding=True, dynamic_finding=False, mitigation=None, test=test)
                    findings.append(finding)
        return findings

    @staticmethod
    def convert_status(wiz_status) -> dict:
        '\n        Convert the Wiz Status to a dict of Finding status flags.\n\n        - Open-> Active = True\n        - Other statuses that may exist...\n        '
        if ((status := wiz_status) is not None):
            if (status.upper() == 'OPEN'):
                return {'active': True}
            if (status.upper() == 'RESOLVED'):
                return {'active': False, 'is_mitigated': True}
            if (status.upper() == 'IGNORED'):
                return {'active': False, 'out_of_scope': True}
            if (status.upper() == 'IN_PROGRESS'):
                return {'active': True}
        return {'active': True}
