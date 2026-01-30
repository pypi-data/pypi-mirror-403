# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

'Parser for OpenReports (https://github.com/openreports/reports-api) vulnerability scan reports'
import json
import logging
from norm_findings.stubs.models import Finding
from norm_findings.parsers.parser_test import ParserTest
logger = logging.getLogger(__name__)
OPENREPORTS_SEVERITIES = {'critical': 'Critical', 'high': 'High', 'medium': 'Medium', 'low': 'Low', 'info': 'Info'}
DESCRIPTION_TEMPLATE = '{message}\n\n**Category:** {category}\n**Policy:** {policy}\n**Result:** {result}\n**Source:** {source}\n**Package Name:** {pkg_name}\n**Installed Version:** {installed_version}\n**Primary URL:** {primary_url}\n'

class OpenreportsParser():

    def get_scan_types(self):
        return ['OpenReports']

    def get_label_for_scan_types(self, scan_type):
        return 'OpenReports'

    def get_description_for_scan_types(self, scan_type):
        return 'Import OpenReports JSON report.'

    def get_findings(self, scan_file, test):
        scan_data = scan_file.read()
        try:
            data = json.loads(str(scan_data, 'utf-8'))
        except Exception:
            data = json.loads(scan_data)
        if (data is None):
            return []
        findings = []
        reports = []
        if isinstance(data, dict):
            if ((data.get('kind') == 'List') and ('items' in data)):
                reports = data['items']
            elif (data.get('kind') == 'Report'):
                reports = [data]
        elif isinstance(data, list):
            reports = data
        for report in reports:
            if ((not isinstance(report, dict)) or (report.get('kind') != 'Report')):
                continue
            findings.extend(self._parse_report(test, report))
        return findings

    def get_tests(self, scan_type, handle):
        try:
            data = json.load(handle)
        except Exception:
            handle.seek(0)
            scan_data = handle.read()
            try:
                data = json.loads(str(scan_data, 'utf-8'))
            except Exception:
                data = json.loads(scan_data)
        if (data is None):
            return []
        reports = []
        if isinstance(data, dict):
            if ((data.get('kind') == 'List') and ('items' in data)):
                reports = data['items']
            elif (data.get('kind') == 'Report'):
                reports = [data]
        elif isinstance(data, list):
            reports = data
        sources_found = set()
        for report in reports:
            if ((not isinstance(report, dict)) or (report.get('kind') != 'Report')):
                continue
            for result in report.get('results', []):
                source = result.get('source', 'OpenReports')
                sources_found.add(source)
        tests = []
        for source in sorted(sources_found):
            test = ParserTest(name=source, parser_type=source, version=None)
            test.findings = []
            for report in reports:
                if ((not isinstance(report, dict)) or (report.get('kind') != 'Report')):
                    continue
                findings = self._parse_report_for_source(test, report, source)
                test.findings.extend(findings)
            tests.append(test)
        return tests

    def _parse_report(self, test, report):
        findings = []
        metadata = report.get('metadata', {})
        report_name = metadata.get('name', '')
        namespace = metadata.get('namespace', '')
        report_uid = metadata.get('uid', '')
        scope = report.get('scope', {})
        scope_kind = scope.get('kind', '')
        scope_name = scope.get('name', '')
        service_name = (f'{namespace}/{scope_kind}/{scope_name}' if namespace else f'{scope_kind}/{scope_name}')
        results = report.get('results', [])
        for result in results:
            if (not isinstance(result, dict)):
                continue
            finding = self._create_finding_from_result(test, result, service_name, report_name, report_uid)
            if finding:
                findings.append(finding)
        return findings

    def _parse_report_for_source(self, test, report, source_filter):
        findings = []
        metadata = report.get('metadata', {})
        report_name = metadata.get('name', '')
        namespace = metadata.get('namespace', '')
        report_uid = metadata.get('uid', '')
        scope = report.get('scope', {})
        scope_kind = scope.get('kind', '')
        scope_name = scope.get('name', '')
        service_name = (f'{namespace}/{scope_kind}/{scope_name}' if namespace else f'{scope_kind}/{scope_name}')
        results = report.get('results', [])
        for result in results:
            if (not isinstance(result, dict)):
                continue
            result_source = result.get('source', 'OpenReports')
            if (result_source != source_filter):
                continue
            finding = self._create_finding_from_result(None, result, service_name, report_name, report_uid)
            if finding:
                findings.append(finding)
        return findings

    def _create_finding_from_result(self, test, result, service_name, report_name, report_uid):
        try:
            message = result.get('message', '')
            category = result.get('category', '')
            policy = result.get('policy', '')
            result_status = result.get('result', '')
            severity = result.get('severity', 'info').lower()
            source = result.get('source', '')
            properties = result.get('properties', {})
            pkg_name = properties.get('pkgName', '')
            installed_version = properties.get('installedVersion', '')
            fixed_version = properties.get('fixedVersion', '')
            primary_url = properties.get('primaryURL', '')
            severity_normalized = OPENREPORTS_SEVERITIES.get(severity, 'Info')
            title = (f'{policy} in {pkg_name}' if policy.startswith('CVE-') else f'{policy}: {message}')
            description = DESCRIPTION_TEMPLATE.format(message=message, category=category, policy=policy, result=result_status, source=source, pkg_name=pkg_name, installed_version=installed_version, primary_url=primary_url)
            fix_available = bool((fixed_version and fixed_version.strip()))
            mitigation = (f'Upgrade to version: {fixed_version}' if fixed_version else '')
            references = (primary_url or '')
            active = (result_status not in {'skip', 'pass'})
            verified = (result_status in {'fail', 'warn'})
            finding = Finding(test=test, title=title, description=description, severity=severity_normalized, references=references, mitigation=mitigation, component_name=pkg_name, component_version=installed_version, service=service_name, active=active, verified=verified, static_finding=True, dynamic_finding=False, fix_available=fix_available, fix_version=(fixed_version or None))
            tags = [category, source]
            scope_kind = (service_name.split('/')[1] if ('/' in service_name) else '')
            if scope_kind:
                tags.append(scope_kind)
            finding.unsaved_tags = tags
            if policy.startswith('CVE-'):
                finding.unsaved_vulnerability_ids = [policy]
            finding.vuln_id_from_tool = policy
            return finding
        except KeyError as exc:
            logger.warning('Failed to parse OpenReports result due to missing key: %r', exc)
            return None
        except Exception as exc:
            logger.warning('Failed to parse OpenReports result: %r', exc)
            return None
