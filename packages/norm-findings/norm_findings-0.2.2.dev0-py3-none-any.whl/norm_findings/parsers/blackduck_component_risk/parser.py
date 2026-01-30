# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from norm_findings.stubs.models import Finding
from .importer import BlackduckCRImporter

class BlackduckComponentRiskParser():
    '\n    Can import as exported from Blackduck:\n    - from a zip file containing a security.csv, sources.csv and components.csv\n    '

    def get_scan_types(self):
        return ['Blackduck Component Risk']

    def get_label_for_scan_types(self, scan_type):
        return 'Blackduck Component Risk'

    def get_description_for_scan_types(self, scan_type):
        return 'Upload the zip file containing the security.csv and files.csv.'

    def get_findings(self, scan_file, test):
        '\n        Function initializes the parser with a file and returns the items.\n        :param filename: Input in Defect Dojo\n        :param test:\n        '
        (components, securities, sources) = self.import_data(scan_file)
        return self.ingest_findings(components, securities, sources, test)

    def import_data(self, filename) -> (dict, dict, dict):
        '\n        Calls the Importer from dojo/tools/blackduck_component_risk/importer to\n        parse through the zip file and export needed information from the\n        three relevant files (security, source and components).\n        :param filename: Name of the zipfile. Passed in via Defect Dojo\n        :return: Returns a tuple of dictionaries, Components and Securities.\n        '
        importer = BlackduckCRImporter()
        (components, securities, sources) = importer.parse_findings(filename)
        return (components, securities, sources)

    def ingest_findings(self, components, securities, sources, test):
        '\n        Takes the components and securities from the importer that parsed the zip file, and\n        iterates over them, creating findings.\n        :param components: Dictionary containing all components from the components csv\n        :param securities: Dictionary containing all security vulnerabilities for each component\n        :param sources: Dictionary containing all sources data from the sources csv\n        :param test:\n        :return:\n        '
        items = []
        license_risk = []
        for (component_id, component) in components.items():
            source = {}
            for (source_id, src) in sources.items():
                if (source_id in component_id):
                    source = src
            if (component.get('Component policy status') == 'In Violation'):
                title = self.license_title(component)
                description = self.license_description(component, source)
                severity = 'High'
                mitigation = self.license_mitigation(component)
                fix_available = bool(mitigation)
                impact = 'N/A'
                references = self.license_references(component)
                finding = Finding(title=title, test=test, description=description, severity=severity, mitigation=mitigation, impact=impact, references=references, static_finding=True, unique_id_from_tool=component_id, fix_available=fix_available)
                license_risk.append(finding)
            elif ('None' not in self.license_severity(component)):
                title = ('Review ' + self.license_title(component))
                description = self.license_description(component, source)
                severity = self.license_severity(component)
                mitigation = self.license_mitigation(component, violation=False)
                fix_available = bool(mitigation)
                impact = 'N/A'
                references = self.license_references(component)
                finding = Finding(title=title, test=test, description=description, severity=severity, mitigation=mitigation, impact=impact, references=references, static_finding=True, unique_id_from_tool=component_id, fix_available=fix_available)
                license_risk.append(finding)
        items.extend(license_risk)
        security_risk = []
        for (component_id, vulns) in securities.items():
            title = self.security_title(vulns)
            description = self.security_description(vulns)
            severity = self.security_severity(vulns)
            mitigation = self.security_mitigation(vulns)
            fix_available = bool(mitigation)
            impact = self.security_impact(vulns)
            references = self.security_references(vulns)
            file_path = self.security_filepath(vulns)
            finding = Finding(title=title, test=test, description=description, severity=severity, mitigation=mitigation, impact=impact, references=references, static_finding=True, file_path=file_path, unique_id_from_tool=component_id, fix_available=fix_available)
            security_risk.append(finding)
        items.extend(security_risk)
        return items

    def license_title(self, component):
        "\n        Uses the Component name and Component version name. The Origin id is sometimes blank,\n        however it seems that component name and version name isn't.\n        :param component: Dictionary containing all components.\n        :return:\n        "
        return 'License Risk: {}:{}'.format(component.get('Component name'), component.get('Component version name'))

    def license_description(self, component, source):
        '\n        Pulls out all important information from the components CSV regarding the License in use.\n        :param component: Dictionary containing all components.\n        :return:\n        '
        desc = '**License Name:** {}  \n'.format(component.get('License names'))
        desc += '**License Families:** {}  \n'.format(component.get('License families'))
        desc += '**License Usage:** {}  \n'.format(component.get('Usage'))
        desc += '**License Origin name:** {} \n'.format(component.get('Origin name'))
        desc += '**License Origin id:** {} \n'.format(component.get('Origin id'))
        desc += '**Match type:** {}\n'.format(component.get('Match type'))
        try:
            desc += '**Path:** {}\n'.format(source.get('Path'))
            desc += '**Archive context:** {}\n'.format(source.get('Archive context'))
            desc += '**Scan:** {}\n'.format(source.get('Scan'))
        except KeyError:
            desc += '**Path:** Unable to find path in source data.'
            desc += '**Archive context:** Unable to find archive context in source data.'
            desc += '**Scan:** Unable to find scan in source data.'
        return desc

    def license_mitigation(self, component, *, violation=True):
        '\n        Uses Component name and Component version name to display the package.\n        :param component: Dictionary containing all components.\n        :param violation: Boolean indicating if this is a violation or for review\n        :return:\n        '
        mit = ''
        if violation:
            mit = 'Package has a license that is In Violation and should not be used: {}:{}.  '.format(component.get('Component name'), component.get('Component version name'))
            mit += 'Please use another component with an acceptable license.'
        else:
            mit = 'Package has a potential license risk and should be reviewed: {}:{}. '.format(component.get('Component name'), component.get('Component version name'))
            mit += 'A legal review may indicate that another component should be used with an acceptable license.'
        return mit

    def license_references(self, component):
        return '**Project:** {}\n'.format(component.get('Project path'))

    def security_title(self, vulns):
        '\n        Creates the Title using the Component name and Component version name.\n        These should be identical for each vuln in the list.\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        return 'Security Risk: {}:{}'.format(vulns[0]['Component name'], vulns[0]['Component version name'])

    def security_description(self, vulns):
        '\n        Markdown formated description that displays information about each CVE found in the\n        csv file for a given component.\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        desc = '#Vulnerabilities \nThis component version contains the following vulnerabilities:\n\n'
        for vuln in vulns:
            desc += '###{}  \n'.format(vuln['Vulnerability id'])
            desc += '**Base Score:** {} \n**Exploitability:** {} \n**Impact:** {}\n'.format(vuln['Base score'], vuln['Exploitability'], vuln['Impact'])
            if vuln['URL']:
                desc += '**URL:** [{}]({})\n'.format(vuln['Vulnerability id'], vuln['URL'])
            desc += '**Description:** {}\n'.format(vuln['Description'])
        return desc

    def license_severity(self, component):
        '\n        Iterates over all base_scores of each vulnerability and picks the max. A map is used to\n        map the all-caps format of the CSV with the case that Defect Dojo expects.\n        (Could use a .lower() or ignore_case during comparison)\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        severity_map = {'HIGH': 'High', 'MEDIUM': 'Medium', 'LOW': 'Low', 'INFO': 'Info', 'CRITICAL': 'Critical', 'OK': 'None'}
        sev = 'None'
        try:
            sev = severity_map[component.get('License Risk')]
        except KeyError:
            sev = 'None'
        return sev

    def security_severity(self, vulns):
        '\n        Iterates over all base_scores of each vulnerability and picks the max. A map is used to\n        map the all-caps format of the CSV with the case that Defect Dojo expects.\n        (Could use a .lower() or ignore_case during comparison)\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        severity_map = {'HIGH': 'High', 'MEDIUM': 'Medium', 'LOW': 'Low', 'INFO': 'Info', 'CRITICAL': 'Critical'}
        max_severity = 0.0
        sev = 'Info'
        for vuln in vulns:
            if (float(vuln['Base score']) > max_severity):
                max_severity = float(vuln['Base score'])
                sev = severity_map[vuln['Security Risk']]
        return sev

    def security_mitigation(self, vulns):
        '\n        Mitigation is always "update package", that the entire point of Blackduck, to identify\n        when projects are using vulnerable versions of components. Mitigation is to update the\n        package. Identifies the component with name:version_name.\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        return 'Update component {}:{} to a secure version'.format(vulns[0]['Component name'], vulns[0]['Component version name'])

    def security_impact(self, vulns):
        '\n        Each vuln has an impact ratiing, so I figured I would iterate over and pull out the\n        largest value.\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        max_impact = 0.0
        for vuln in vulns:
            max_impact = max(max_impact, float(vuln['Impact']))
        return max_impact

    def security_references(self, vulns):
        '\n        Takes all of the URL fields out of the csv, not all findings will have a URL, so it will\n        only create it for those that do.\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        references = '**Project:** {}\n'.format(vulns[0]['Project path'])
        for vuln in vulns:
            if vuln['URL']:
                references += '{}: [{}]({})\n'.format(vuln['Vulnerability id'], vuln['URL'], vuln['URL'])
        return references

    def security_filepath(self, vulns):
        '\n        The origin name (maven, github, npmjs, etc) and the component origin id is used. However,\n        not all items will have an origin id, so to try to still match as closely as possible,\n        "component_name/version" is used.\n        1. origin:component_origin_id\n        2. origin:component_name/version\n        :param vulns: Dictionary {component_version_identifier: [vulns]}\n        :return:\n        '
        if (not vulns[0]['Component origin id']):
            component_key = '{}/{}'.format(vulns[0]['Component name'], vulns[0]['Component version name'])
        else:
            component_key = vulns[0]['Component origin id']
        return '{}:{}'.format(vulns[0]['Component origin name'], component_key)
