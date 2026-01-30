# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

import datetime
import json
import logging
from dateutil import parser
from defusedxml import ElementTree
from norm_findings.stubs.models import Finding
from norm_findings.stubs.utils import add_language
logger = logging.getLogger(__name__)

class CheckmarxParser():

    def get_fields(self) -> list[str]:
        '\n        Return the list of fields used in the Checkmarx Parser.\n\n        Fields:\n        - title: Constructed from output of Checkmarx Scanner.\n        - cwe: Set to cwe outputted by Checkmarx Parser.\n        - active: Set to boolean value based on state returned by Checkmarx Parser.\n        - verified: Set to boolean value based on state returned by Checkmarx Parser.\n        - false_p: Set to boolean value based on "falsePositive" returned by Checkmarx Parser.\n        - description: Made from combining linenumber, column, source object, and number.\n        - severity: Set to severity outputted by Checkmarx Scanner.\n        - file_path: Set to filename outputted by Checkmarx Scanner.\n        - date: Set to date outputted by Checkmarx Scanner.\n        - static_finding: Set to true.\n        - nb_occurences: Inittially set to 1 and then updated accordingly.\n        - line: Set to line outputted by Checkmarx Scanner.\n        - unique_id_from_tool: [If mode set to detailed] Set to the unique pathId outputted by Checkmarx Parser.\n        - sast_source_object: [If mode set to detailed] Set to sourceObject outputted by Checkmarx Parser.\n        - sast_sink_object: [If mode set to detailed] Set to sinkObject outputted by Checkmarx Parser.\n        - sast_source_line: [If mode set to detailed] Set to sourceLineNumber outputted by Checkmarx Parser.\n        - sast_source_file_path: [If mode set to detailed] Set to sourceFilename outputted by Checkmarx Parser.\n        - vuln_id_from_tool: Set to id from Checkmarx Scanner.\n        - component_name: Set to value within the "name" returned from the Checkmarx Scanner.\n        - component_version: Set to value within the "name" returned from the Checkmarx Scanner.\n        '
        return ['title', 'cwe', 'active', 'verified', 'false_p', 'description', 'severity', 'file_path', 'date', 'static_finding', 'nb_occurences', 'line', 'unique_id_from_tool', 'sast_source_object', 'sast_sink_object', 'sast_source_line', 'sast_source_file_path', 'vuln_id_from_tool', 'component_name', 'component_version']

    def get_dedupe_fields(self) -> list[str]:
        '\n        Return the list of fields used for deduplication in the Checkmarx Parser.\n\n        Fields:\n        - cwe: Set to cwe outputted by Checkmarx Parser.\n        - severity: Set to severity outputted by Checkmarx Scanner.\n        - file_path: Set to filename outputted by Checkmarx Scanner.\n        '
        return ['cwe', 'severity', 'file_path']

    def get_scan_types(self):
        return ['Checkmarx Scan', 'Checkmarx Scan detailed']

    def get_label_for_scan_types(self, scan_type):
        return scan_type

    def get_description_for_scan_types(self, scan_type):
        if (scan_type == 'Checkmarx Scan'):
            return 'Simple Report. Aggregates vulnerabilities per categories, cwe, name, sinkFilename'
        return 'Detailed Report. Import all vulnerabilities from checkmarx without aggregation'
    mode = None

    def set_mode(self, mode):
        self.mode = mode

    def _get_findings_xml(self, filename, test):
        '\n        ----------------------------------------\n        Structure of the checkmarx xml report:\n        ----------------------------------------\n        - Query:\n        the kind of vulnerabilities. Contains for example cweId\n        - Result: One vulnerability in checkmarx = 1 pathId\n        Includes filename and linenumber from source of vulnerability (start of the attack vector)\n        - Path: There should be only one.Parent tag of Pathnodes\n        - Pathnode: all the calls from the source (start) to the sink (end) of the attack vector\n        '
        cxscan = ElementTree.parse(filename)
        root = cxscan.getroot()
        dupes = {}
        language_list = {}
        vuln_ids_from_tool = {}
        for query in root.findall('Query'):
            (_name, _cwe, categories, _queryId) = self.getQueryElements(query)
            language = ''
            findingdetail = ''
            group = ''
            find_date = parser.parse(root.get('ScanStart')).date()
            if (query.get('Language') is not None):
                language = query.get('Language')
            if (query.get('group') is not None):
                group = query.get('group').replace('_', ' ')
            for result in query.findall('Result'):
                if (categories is not None):
                    findingdetail = f'''{findingdetail}**Category:** {categories}
'''
                if (language is not None):
                    findingdetail = f'''{findingdetail}**Language:** {language}
'''
                    if (language not in language_list):
                        language_list[language] = 1
                    else:
                        language_list[language] += 1
                if (group is not None):
                    findingdetail = f'''{findingdetail}**Group:** {group}
'''
                if (result.get('Status') is not None):
                    findingdetail = '{}**Status:** {}\n'.format(findingdetail, result.get('Status'))
                deeplink = '[{}]({})'.format(result.get('DeepLink'), result.get('DeepLink'))
                findingdetail = f'''{findingdetail}**Finding Link:** {deeplink}
'''
                if (self.mode == 'detailed'):
                    self._process_result_detailed(test, dupes, findingdetail, query, result, find_date)
                else:
                    self._process_result_file_name_aggregated(test, dupes, vuln_ids_from_tool, findingdetail, query, result, find_date)
                findingdetail = ''
            if (self.mode != 'detailed'):
                for key in list(dupes):
                    dupes[key].vuln_id_from_tool = ','.join(vuln_ids_from_tool[key])[:500]
        for (lang, file) in language_list.items():
            add_language(test.engagement.product, lang, files=file)
        return list(dupes.values())

    def _process_result_file_name_aggregated(self, test, dupes, vuln_ids_from_tool, findingdetail, query, result, find_date):
        '\n        Process one result = one pathId for default "Checkmarx Scan"\n        Create the finding and add it into the dupes list\n        If a vuln with the same file_path was found before, updates the description\n        '
        (_name, cwe, _categories, queryId) = self.getQueryElements(query)
        titleStart = query.get('name').replace('_', ' ')
        (description, lastPathnode) = self.get_description_file_name_aggregated(query, result)
        sinkFilename = lastPathnode.find('FileName').text
        title = ('{} ({})'.format(titleStart, sinkFilename.split('/')[(- 1)]) if sinkFilename else titleStart)
        false_p = result.get('FalsePositive')
        sev = result.get('Severity')
        aggregateKeys = f'{cwe}{sev}{sinkFilename}'
        state = result.get('state')
        active = self.isActive(state)
        verified = self.isVerified(state)
        if (aggregateKeys not in dupes):
            find = Finding(title=title, cwe=int(cwe), test=test, active=active, verified=verified, false_p=(false_p == 'True'), description=(findingdetail + description), severity=sev, file_path=sinkFilename, date=find_date, static_finding=True, nb_occurences=1)
            dupes[aggregateKeys] = find
            vuln_ids_from_tool[aggregateKeys] = [queryId]
        else:
            find = dupes[aggregateKeys]
            find.nb_occurences += 1
            if (find.nb_occurences == 2):
                find.description = f'''### 1. {find.title}
{find.description}'''
            find.description = f'''{find.description}

-----
### {find.nb_occurences}. {title}
{findingdetail}
{description}'''
            if (queryId not in vuln_ids_from_tool[aggregateKeys]):
                vuln_ids_from_tool[aggregateKeys].append(queryId)
            if (false_p == 'False'):
                dupes[aggregateKeys].false_p = False
            if active:
                dupes[aggregateKeys].active = True
            if verified:
                dupes[aggregateKeys].verified = True

    def get_description_file_name_aggregated(self, query, result):
        description = ''
        for path in result.findall('Path'):
            firstPathnode = True
            for pathnode in path.findall('PathNode'):
                if firstPathnode:
                    (sourceFilename, sourceLineNumber, sourceObject) = self.get_pathnode_elements(pathnode)
                    firstPathnode = False
        (sinkFilename, sinkLineNumber, sinkObject) = self.get_pathnode_elements(pathnode)
        description = f'''<b>Source file: </b>{sourceFilename} (line {sourceLineNumber})
<b>Source object: </b> {sourceObject}'''
        description = f'''{description}
<b>Sink file: </b>{sinkFilename} (line {sinkLineNumber})
<b>Sink object: </b> {sinkObject}'''
        return (description, pathnode)

    def _process_result_detailed(self, test, dupes, findingdetail, query, result, find_date):
        '\n        Process one result = one pathId for scanner "Checkmarx Scan detailed"\n        Create the finding and add it into the dupes list\n        '
        (name, cwe, categories, queryId) = self.getQueryElements(query)
        sev = result.get('Severity')
        title = query.get('name').replace('_', ' ')
        state = result.get('state')
        paths = result.findall('Path')
        if (len(paths) > 1):
            logger.warning((('Checkmarx scan: more than one path found: ' + str(len(paths))) + '. Only the last one will be used'))
        for path in paths:
            sourceFilename = ''
            sinkFilename = ''
            sourceLineNumber = None
            sinkLineNumber = None
            sourceObject = ''
            sinkObject = ''
            similarityId = str(path.get('SimilarityId'))
            path_id = str(path.get('PathId'))
            pathId = (similarityId + path_id)
            findingdetail = f'''{findingdetail}-----
'''
            for pathnode in path.findall('PathNode'):
                findingdetail = self.get_description_detailed(pathnode, findingdetail)
                nodeId = pathnode.find('NodeId').text
                if (nodeId == '1'):
                    (sourceFilename, sourceLineNumber, sourceObject) = self.get_pathnode_elements(pathnode)
            (sinkFilename, sinkLineNumber, sinkObject) = self.get_pathnode_elements(pathnode)
            aggregateKeys = f'{categories}{cwe}{name}{sinkFilename}{pathId}'
            if (title and sinkFilename):
                title = '{} ({})'.format(title, sinkFilename.split('/')[(- 1)])
            find = Finding(title=title, cwe=int(cwe), test=test, active=self.isActive(state), verified=self.isVerified(state), false_p=(result.get('FalsePositive') == 'True'), description=findingdetail, severity=sev, file_path=sinkFilename, line=sinkLineNumber, date=find_date, static_finding=True, unique_id_from_tool=pathId, sast_source_object=sourceObject, sast_sink_object=sinkObject, sast_source_line=sourceLineNumber, sast_source_file_path=sourceFilename, vuln_id_from_tool=queryId)
        dupes[aggregateKeys] = find

    def get_pathnode_elements(self, pathnode):
        return (pathnode.find('FileName').text, int(pathnode.find('Line').text), pathnode.find('Name').text)

    def get_description_detailed(self, pathnode, findingdetail):
        if (pathnode.find('Line').text is not None):
            findingdetail = '{}**Line Number:** {}\n'.format(findingdetail, pathnode.find('Line').text)
        if (pathnode.find('Column').text is not None):
            findingdetail = '{}**Column:** {}\n'.format(findingdetail, pathnode.find('Column').text)
        if (pathnode.find('Name').text is not None):
            findingdetail = '{}**Source Object:** {}\n'.format(findingdetail, pathnode.find('Name').text)
        for codefragment in pathnode.findall('Snippet/Line'):
            findingdetail = '{}**Number:** {}\n**Code:** {}\n'.format(findingdetail, codefragment.find('Number').text, codefragment.find('Code').text.strip())
        return f'''{findingdetail}-----
'''

    def getQueryElements(self, query):
        categories = ''
        name = query.get('name')
        cwe = query.get('cweId')
        queryId = query.get('id')
        if (query.get('categories') is not None):
            categories = query.get('categories')
        return (name, cwe, categories, queryId)

    def isActive(self, state):
        'Map checkmarx report state to active/inactive status'
        activeStates = ['0', '2', '3', '4']
        return (state in activeStates)

    def isVerified(self, state):
        verifiedStates = ['2', '3']
        return (state in verifiedStates)

    def get_findings(self, scan_file, test):
        if scan_file.name.strip().lower().endswith('.json'):
            return self._get_findings_json(scan_file, test)
        return self._get_findings_xml(scan_file, test)

    def _parse_date(self, value):
        if isinstance(value, str):
            return parser.parse(value).date()
        if (isinstance(value, dict) and isinstance(value.get('seconds'), int)):
            return datetime.datetime.fromtimestamp(value.get('seconds'), datetime.timezone.utc).date()
        return None

    def _get_findings_json(self, file, test):
        ''
        data = json.load(file)
        findings = []
        results = data.get('scanResults', [])
        for result_type in results:
            if ((result_type == 'sast') and (results.get(result_type) is not None)):
                for language in results[result_type].get('languages', []):
                    for query in language.get('queries', []):
                        descriptiondetails = query.get('description', '')
                        title = query.get('queryName').replace('_', ' ')
                        if query.get('groupName'):
                            query.get('groupName').replace('_', ' ')
                        for vulnerability in query.get('vulnerabilities', []):
                            finding = Finding(description=descriptiondetails, title=title, date=self._parse_date(vulnerability.get('firstFoundDate')), severity=vulnerability.get('severity').title(), active=(vulnerability.get('status') != 'Not exploitable'), verified=(vulnerability.get('status') != 'To verify'), test=test, cwe=vulnerability.get('cweId'), static_finding=True)
                            if vulnerability.get('id'):
                                finding.unique_id_from_tool = vulnerability.get('id')
                            else:
                                finding.unique_id_from_tool = str(vulnerability.get('similarityId'))
                            if vulnerability.get('nodes'):
                                last_node = vulnerability['nodes'][(- 1)]
                                finding.file_path = last_node.get('fileName')
                                finding.line = last_node.get('line')
                            finding.unsaved_tags = [result_type]
                            findings.append(finding)
            if ((result_type == 'sca') and (results.get(result_type) is not None)):
                for package in results[result_type].get('packages', []):
                    component_name = package.get('name').split('-')[(- 2)]
                    component_version = package.get('name').split('-')[(- 1)]
                    for vulnerability in package.get('vulnerabilities', []):
                        cve = vulnerability.get('cveId')
                        finding = Finding(title=f'{component_name}:{component_version} | {cve}', description=vulnerability.get('description'), date=self._parse_date(vulnerability.get('firstFoundDate')), severity=vulnerability.get('severity').title(), active=(vulnerability.get('status') != 'Not exploitable'), verified=(vulnerability.get('state') != 'To verify'), component_name=component_name, component_version=component_version, test=test, cwe=int(vulnerability.get('cwe', 0)), static_finding=True)
                        if vulnerability.get('cveId'):
                            finding.unsaved_vulnerability_ids = [vulnerability.get('cveId')]
                        if vulnerability.get('id'):
                            finding.unique_id_from_tool = vulnerability.get('id')
                        else:
                            finding.unique_id_from_tool = str(vulnerability.get('similarityId'))
                        finding.unsaved_tags = [result_type]
                        findings.append(finding)
            if ((result_type == 'kics') and (results.get(result_type) is not None)):
                for kics_type in results[result_type].get('results', []):
                    name = kics_type.get('name')
                    for vulnerability in kics_type.get('vulnerabilities', []):
                        finding = Finding(title=f"{name} | {vulnerability.get('issueType')}", description=vulnerability.get('description'), date=self._parse_date(vulnerability.get('firstFoundDate')), severity=vulnerability.get('severity').title(), active=(vulnerability.get('status') != 'Not exploitable'), verified=(vulnerability.get('state') != 'To verify'), file_path=vulnerability.get('fileName'), line=vulnerability.get('line', 0), severity_justification=vulnerability.get('actualValue'), test=test, static_finding=True)
                        if vulnerability.get('id'):
                            finding.unique_id_from_tool = vulnerability.get('id')
                        else:
                            finding.unique_id_from_tool = str(vulnerability.get('similarityId'))
                        finding.unsaved_tags = [result_type, name]
                        findings.append(finding)
        return findings
