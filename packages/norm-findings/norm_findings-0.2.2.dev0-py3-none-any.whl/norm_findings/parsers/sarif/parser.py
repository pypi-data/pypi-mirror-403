# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import json
import logging
import re
import textwrap
import dateutil.parser
from norm_findings.stubs.django.utils.translation import gettext as _
from norm_findings.stubs.models import Finding
from norm_findings.parsers.parser_test import ParserTest
logger = logging.getLogger(__name__)
CWE_REGEX = 'cwe-\\d+'

class SarifParser():
    '\n    OASIS Static Analysis Results Interchange Format (SARIF) for version 2.1.0 only.\n\n    https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=sarif\n    '

    def get_fields(self) -> list[str]:
        "\n        Return the list of fields used in the Sarif Parser\n\n        Fields:\n        - title: Made using rule and id from Sarif scanner.\n        - severity: Set to severity from Sarif Scanner converted to Defect Dojo format.\n        - description: Made by combining message, location, and rule from Sarif Scanner.\n        - static_finding: Set to true.\n        - dynamic_finding: Set to false.\n        - false_p: Set to true or false based on suppression status from Sarif scanner.\n        - active: Set to true or false based on suppression status from Sarif scanner.\n        - file_path: Set to physical location from Sarif scanner.\n        - line: Set to start line from Sarif scanner.\n        - vuln_id_from_tool: Set to rule id from Sarif scanner.\n        - cwe: Set to the cwe values outputted from Sarif Scanner.\n        - cvssv3: Set to properties and securitiy-severity from Sarif scanner if available.\n        - cvssv3_score: Set to properties and securitiy-severity from Sarif scanner if available.\n        - mitigation: Set to altered version of finding's description.\n        - date: Set to the date outputted from Sarif Scanner converted to datetime.\n        - tags: Set to tags from Sarif scanner.\n        - unique_id_from_tool: Set to the hash fingerpring value outputted from Sarif Scanner.\n\n        NOTE: This parser supports tags.\n        "
        return ['title', 'severity', 'description', 'static_finding', 'dynamic_finding', 'false_p', 'active', 'file_path', 'line', 'vuln_id_from_tool', 'cwe', 'cvssv3', 'cvssv3_score', 'mitigation', 'date', 'tags', 'unique_id_from_tool']

    def get_dedupe_fields(self) -> list[str]:
        "\n        Return the list of dedupe fields used in the Sarif Parser\n\n        Fields:\n        - title: Made using rule and id from Sarif scanner.\n        - cwe: Set to the cwe values outputted from Sarif Scanner.\n        - line: Set to start line from Sarif scanner.\n        - file_path: Set to physical location from Sarif scanner.\n        - description: Made by combining message, location, and rule from Sarif Scanner.\n\n        NOTE: uses legacy dedupe: ['title', 'cwe', 'line', 'file_path', 'description']\n        "
        return ['title', 'cwe', 'line', 'file_path', 'description']

    def get_scan_types(self):
        return ['SARIF']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        return 'SARIF report file can be imported in SARIF format.'

    def get_findings(self, scan_file, test):
        'For simple interface of parser contract we just aggregate everything'
        tree = json.load(scan_file)
        items = []
        for run in tree.get('runs', []):
            items.extend(self.__get_items_from_run(run))
        return items

    def get_tests(self, scan_type, handle):
        tree = json.load(handle)
        tests = []
        for run in tree.get('runs', []):
            test = ParserTest(name=run['tool']['driver']['name'], parser_type=run['tool']['driver']['name'], version=run['tool']['driver'].get('version'))
            test.findings = self.__get_items_from_run(run)
            tests.append(test)
        return tests

    def __get_items_from_run(self, run):
        items = []
        rules = get_rules(run)
        artifacts = get_artifacts(run)
        run_date = self.__get_last_invocation_date(run)
        for result in run.get('results', []):
            result_items = self.get_items_from_result(result, rules, artifacts, run_date)
            if result_items:
                items.extend(result_items)
        return items

    def __get_last_invocation_date(self, data):
        invocations = data.get('invocations', [])
        if (len(invocations) == 0):
            return None
        raw_date = invocations[(- 1)].get('endTimeUtc')
        if (raw_date is None):
            return None
        return dateutil.parser.isoparse(raw_date)

    def get_items_from_result(self, result, rules, artifacts, run_date):
        '\n        Main method to extract findings from a SARIF result.\n        This method can be overridden by subclasses for custom behavior.\n        '
        kind = result.get('kind', 'fail')
        if (kind != 'fail'):
            return None
        suppressed = False
        if result.get('suppressions'):
            suppressed = True
        files = []
        if ('locations' in result):
            for location in result['locations']:
                file_path = None
                line = None
                if ('physicalLocation' in location):
                    file_path = location['physicalLocation']['artifactLocation']['uri']
                    if ('region' in location['physicalLocation']):
                        if ('byteOffset' in location['physicalLocation']['region']):
                            pass
                        else:
                            line = location['physicalLocation']['region']['startLine']
                files.append((file_path, line, location))
        if (not files):
            files.append((None, None, None))
        result_items = []
        for (file_path, line, location) in files:
            rule = rules.get(result.get('ruleId'))
            description = self.get_finding_description(result, rule, location)
            title = self.get_finding_title(result, rule, location)
            (static_finding, dynamic_finding) = self.get_finding_type()
            finding = Finding(title=title, severity=get_severity(result, rule), description=description, static_finding=static_finding, dynamic_finding=dynamic_finding, false_p=suppressed, active=(not suppressed), file_path=file_path, line=line, references=get_references(rule))
            if ('ruleId' in result):
                finding.vuln_id_from_tool = result['ruleId']
                if cve_try(result['ruleId']):
                    finding.unsaved_vulnerability_ids = [cve_try(result['ruleId'])]
            if (rule is not None):
                cwes_extracted = get_rule_cwes(rule)
                if (len(cwes_extracted) > 0):
                    finding.cwe = cwes_extracted[(- 1)]
                if (('properties' in rule) and ('security-severity' in rule['properties'])):
                    try:
                        cvss = float(rule['properties']['security-severity'])
                        severity = cvss_to_severity(cvss)
                        finding.cvssv3_score = cvss
                        finding.severity = severity
                    except ValueError:
                        if (rule['properties']['security-severity'].lower().capitalize() in {'Info', 'Low', 'Medium', 'High', 'Critical'}):
                            finding.severity = rule['properties']['security-severity'].lower().capitalize()
                        else:
                            finding.severity = 'Info'
            cwes_properties_extracted = get_result_cwes_properties(result)
            if (len(cwes_properties_extracted) > 0):
                finding.cwe = cwes_properties_extracted[(- 1)]
            cwes_taxa_extracted = get_result_cwes_taxa(result)
            if (len(cwes_taxa_extracted) > 0):
                finding.cwe = cwes_taxa_extracted[(- 1)]
            custom_cwes = self.get_finding_cwes(result)
            if custom_cwes:
                finding.cwe = custom_cwes[(- 1)]
            if ('fixes' in result):
                finding.mitigation = '\n'.join([fix.get('description', {}).get('text') for fix in result['fixes']])
            if run_date:
                finding.date = run_date
            tags = list(set((get_properties_tags(rule) + get_properties_tags(result))))
            tags = [s.removeprefix('external/cwe/') for s in tags]
            finding.unsaved_tags = tags
            if result.get('fingerprints'):
                hashes = get_fingerprints_hashes(result['fingerprints'])
                first_item = next(iter(hashes.items()))
                finding.unique_id_from_tool = first_item[1]['value']
            elif result.get('partialFingerprints'):
                hashes = get_fingerprints_hashes(result['partialFingerprints'])
                sorted_hashes = sorted(hashes.keys())
                finding.unique_id_from_tool = '|'.join([f"{key}:{hashes[key]['value']}" for key in sorted_hashes])
            self.customize_finding(finding, result, rule, location)
            result_items.append(finding)
        return result_items

    def get_finding_cwes(self, result):
        '\n        Hook method for subclasses to extract custom CWE values from result.\n        Override this method to add custom CWE extraction logic.\n        '
        return []

    def get_finding_title(self, result, rule, location):
        '\n        Get title for the finding. Subclasses can override this method\n        to add custom title formatting. Use super() to get the base title.\n        '
        title = None
        if ('message' in result):
            title = get_message_from_multiformatMessageString(result['message'], rule)
        if ((title is None) and (rule is not None)):
            if ('shortDescription' in rule):
                title = get_message_from_multiformatMessageString(rule['shortDescription'], rule)
            elif ('fullDescription' in rule):
                title = get_message_from_multiformatMessageString(rule['fullDescription'], rule)
            elif ('name' in rule):
                title = rule['name']
            elif ('id' in rule):
                title = rule['id']
        if (title is None):
            msg = 'No information found to create a title'
            raise ValueError(msg)
        return textwrap.shorten(title, 150)

    def get_finding_description(self, result, rule, location):
        '\n        Get description for the finding. Subclasses can override this method\n        to add custom description formatting. Use super() to get the base description.\n        '
        description = ''
        message = ''
        if ('message' in result):
            message = get_message_from_multiformatMessageString(result['message'], rule)
            description += f'''**Result message:** {message}
'''
        if (get_snippet(location) is not None):
            description += f'''**Snippet:**
```
{get_snippet(location)}
```
'''
        if (rule is not None):
            if ('name' in rule):
                description += f'''**{_('Rule name')}:** {rule.get('name')}
'''
            shortDescription = ''
            if ('shortDescription' in rule):
                shortDescription = get_message_from_multiformatMessageString(rule['shortDescription'], rule)
                if (shortDescription != message):
                    description += f'''**{_('Rule short description')}:** {shortDescription}
'''
            if ('fullDescription' in rule):
                fullDescription = get_message_from_multiformatMessageString(rule['fullDescription'], rule)
                if (fullDescription not in {message, shortDescription}):
                    description += f'''**{_('Rule full description')}:** {fullDescription}
'''
        if (len(result.get('codeFlows', [])) > 0):
            description += get_codeFlowsDescription(result['codeFlows'])
        return description.removesuffix('\n')

    def get_finding_type(self):
        '\n        Hook method for subclasses to specify finding type.\n        Returns tuple of (static_finding, dynamic_finding).\n        '
        return (True, False)

    def customize_finding(self, finding, result, rule, location):
        '\n        Hook method for subclasses to customize the finding after creation.\n        Override this method to add custom fields or modify the finding.\n        '

def get_rules(run):
    rules = {}
    rules_array = run['tool']['driver'].get('rules', [])
    if ((len(rules_array) == 0) and (run['tool'].get('extensions') is not None)):
        rules_array = run['tool']['extensions'][0].get('rules', [])
    for item in rules_array:
        rules[item['id']] = item
    return rules

def get_properties_tags(value):
    if (not value):
        return []
    return value.get('properties', {}).get('tags', [])

def search_cwe(value, cwes):
    matches = re.search(CWE_REGEX, value, re.IGNORECASE)
    if matches:
        cwes.append(int(matches[0].split('-')[1]))

def get_rule_cwes(rule):
    cwes = []
    if (('relationships' in rule) and isinstance(rule['relationships'], list)):
        for relationship in rule['relationships']:
            value = relationship['target']['id']
            search_cwe(value, cwes)
        return cwes
    if (('properties' in rule) and ('cwe' in rule['properties'])):
        cwe_values = rule['properties']['cwe']
        if isinstance(cwe_values, list):
            for cwe_value in cwe_values:
                search_cwe(cwe_value, cwes)
        else:
            search_cwe(cwe_values, cwes)
        return cwes
    for tag in get_properties_tags(rule):
        search_cwe(tag, cwes)
    return cwes

def get_result_cwes_properties(result):
    'Some tools like njsscan store the CWE in the properties of the result'
    cwes = []
    if (('properties' in result) and ('cwe' in result['properties'])):
        value = result['properties']['cwe']
        search_cwe(value, cwes)
    return cwes

def get_result_cwes_taxa(result):
    'Extract CWEs from SARIF taxa (official SARIF approach)'
    cwes = []
    if (('taxa' in result) and isinstance(result['taxa'], list)):
        for taxon in result['taxa']:
            if isinstance(taxon, dict):
                tool_component = taxon.get('toolComponent', {})
                if (tool_component.get('name') == 'CWE'):
                    cwe_id = taxon.get('id')
                    if cwe_id:
                        try:
                            cwes.append(int(cwe_id))
                        except ValueError:
                            search_cwe(f'CWE-{cwe_id}', cwes)
    return cwes

def get_artifacts(run):
    artifacts = {}
    for (custom_index, tree_artifact) in enumerate(run.get('artifacts', [])):
        artifacts[tree_artifact.get('index', custom_index)] = tree_artifact
    return artifacts

def get_message_from_multiformatMessageString(data, rule):
    '\n    Get a message from multimessage struct\n\n    See here for the specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/sarif-v2.1.0-os.html#_Toc34317468\n    '
    if ((rule is not None) and ('id' in data)):
        text = rule['messageStrings'][data['id']].get('text')
        arguments = data.get('arguments', [])
        for i in range(6):
            substitution_str = (('{' + str(i)) + '}')
            if (substitution_str in text):
                text = text.replace(substitution_str, arguments[i])
            else:
                return text
        return None
    return data.get('text')

def cve_try(val):
    cveSearch = re.search('(CVE-[0-9]+-[0-9]+)', val, re.IGNORECASE)
    if cveSearch:
        return cveSearch.group(1).upper()
    return None

def get_snippet(location):
    snippet = None
    if (location and ('physicalLocation' in location)):
        if ('region' in location['physicalLocation']):
            if ('snippet' in location['physicalLocation']['region']):
                if ('text' in location['physicalLocation']['region']['snippet']):
                    snippet = location['physicalLocation']['region']['snippet']['text']
        if ((snippet is None) and ('contextRegion' in location['physicalLocation'])):
            if ('snippet' in location['physicalLocation']['contextRegion']):
                if ('text' in location['physicalLocation']['contextRegion']['snippet']):
                    snippet = location['physicalLocation']['contextRegion']['snippet']['text']
    return snippet

def get_codeFlowsDescription(code_flows):
    description = ''
    for codeFlow in code_flows:
        for threadFlow in codeFlow.get('threadFlows', []):
            if ('locations' not in threadFlow):
                continue
            description = f'''**{_('Code flow')}:**
'''
            for (line, location) in enumerate(threadFlow.get('locations', [])):
                physicalLocation = location.get('location', {}).get('physicalLocation', {})
                region = physicalLocation.get('region', {})
                uri = physicalLocation.get('artifactLocation').get('uri')
                start_line = ''
                start_column = ''
                snippet = ''
                if ('startLine' in region):
                    start_line = f":L{region.get('startLine')}"
                if ('startColumn' in region):
                    start_column = f":C{region.get('startColumn')}"
                if ('snippet' in region):
                    snippet = f"	-	{region.get('snippet').get('text')}"
                description += f'''{(line + 1)}. {uri}{start_line}{start_column}{snippet}
'''
                if ('message' in location.get('location', {})):
                    message_field = location.get('location', {}).get('message', {})
                    if ('markdown' in message_field):
                        message = message_field.get('markdown', '')
                    else:
                        message = message_field.get('text', '')
                    description += f'''	{message}
'''
    return description

def get_references(rule):
    reference = None
    if (rule is not None):
        if ('helpUri' in rule):
            reference = rule['helpUri']
        elif ('help' in rule):
            helpText = get_message_from_multiformatMessageString(rule['help'], rule)
            if helpText.startswith('http'):
                reference = helpText
    return reference

def cvss_to_severity(cvss):
    severity_mapping = {1: 'Info', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}
    if (cvss >= 9):
        return severity_mapping.get(5)
    if (cvss >= 7):
        return severity_mapping.get(4)
    if (cvss >= 4):
        return severity_mapping.get(3)
    if (cvss > 0):
        return severity_mapping.get(2)
    return severity_mapping.get(1)

def get_severity(result, rule):
    severity = result.get('level')
    if ((severity is None) and (rule is not None)):
        if ('defaultConfiguration' in rule):
            severity = rule['defaultConfiguration'].get('level')
    if (severity == 'note'):
        return 'Info'
    if (severity == 'warning'):
        return 'Medium'
    if (severity == 'error'):
        return 'High'
    return 'Medium'

def get_fingerprints_hashes(values):
    '\n    Method that generate a `unique_id_from_tool` data from the `fingerprints` attribute.\n     - for now, we take the value of the last version of the first hash method.\n    '
    fingerprints = {}
    for key in values:
        if ('/' in key):
            key_method = key.split('/')[(- 2)]
            key_method_version = int(key.split('/')[(- 1)].replace('v', ''))
        else:
            key_method = key
            key_method_version = 0
        value = values[key]
        if fingerprints.get(key_method):
            if (fingerprints[key_method]['version'] < key_method_version):
                fingerprints[key_method] = {'version': key_method_version, 'value': value}
        else:
            fingerprints[key_method] = {'version': key_method_version, 'value': value}
    return fingerprints
