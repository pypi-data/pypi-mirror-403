# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import json
import logging
import re
import textwrap
from datetime import datetime
import dateutil.parser
from norm_findings.stubs.django.core.exceptions import ValidationError
from norm_findings.stubs.models import Endpoint, Finding
from .importer import BugcrowdApiImporter
SCAN_BUGCROWD_API = 'Bugcrowd API Import'
pattern_title_authorized = re.compile('^[a-zA-Z0-9_\\s+-.]*$')
logger = logging.getLogger(__name__)

class ApiBugcrowdParser():
    'Import from Bugcrowd API /submissions'

    def get_scan_types(self):
        return [SCAN_BUGCROWD_API]

    def get_label_for_scan_types(self, scan_type):
        return SCAN_BUGCROWD_API

    def get_description_for_scan_types(self, scan_type):
        return 'Bugcrowd submissions can be directly imported using the Bugcrowd API. An API Scan Configuration has to be setup in the Product.'

    def requires_file(self, scan_type):
        return False

    def requires_tool_type(self, scan_type):
        return 'Bugcrowd API'

    def api_scan_configuration_hint(self):
        return 'the field <b>Service key 1</b> has to be set with the Bugcrowd program code. <b>Service key 2</b> can be set with the target in the Bugcrowd program (will be url encoded for the api call), if not supplied, will fetch all submissions in the program'

    def get_findings(self, scan_file, test):
        api_scan_config = None
        if (scan_file is None):
            (data, api_scan_config) = BugcrowdApiImporter().get_findings(test)
        else:
            data = json.load(scan_file)
        findings = []
        for entry in data:
            if (not self.include_finding(entry)):
                continue
            if test.api_scan_configuration:
                config = test.api_scan_configuration
                links = 'https://tracker.bugcrowd.com/{}{}'.format(str(config.service_key_1), entry['links']['self'])
            if (api_scan_config is not None):
                links = 'https://tracker.bugcrowd.com/{}{}'.format(str(api_scan_config.service_key_1), entry['links']['self'])
            else:
                links = None
                if (('links' in entry) and ('self' in entry['links'])):
                    links = entry['links']['self']
            bugcrowd_state = entry['attributes']['state']
            entry['attributes']['duplicate']
            bugcrowd_severity = entry['attributes']['severity']
            title = entry['attributes']['title']
            if (not pattern_title_authorized.match(title)):
                char_to_replace = {':': ' ', '"': ' ', '@': 'at'}
                for (key, value) in char_to_replace.items():
                    title = title.replace(key, value)
            date = dateutil.parser.parse(entry['attributes']['submitted_at'])
            bug_url = ''
            bug_endpoint = None
            if entry['attributes']['bug_url']:
                try:
                    if ('://' in entry['attributes']['bug_url']):
                        bug_endpoint = Endpoint.from_uri(entry['attributes']['bug_url'].strip())
                    else:
                        bug_endpoint = Endpoint.from_uri(('//' + entry['attributes']['bug_url'].strip()))
                except ValueError:
                    logger.error('Error parsing bugcrowd bug_url : %s', entry['attributes']['bug_url'].strip())
                bug_url = entry['attributes']['bug_url']
            description = '\n'.join([entry['attributes']['description'], '', 'Bugcrowd details:', f'- Severity: P{bugcrowd_severity}', f'- Bug Url: [{bug_url}]({bug_url})', '', f'Bugcrowd link: [{links}]({links})'])
            mitigation = entry['attributes']['remediation_advice']
            steps_to_reproduce = entry['attributes']['description']
            unique_id_from_tool = entry['id']
            finding = Finding(test=test, title=textwrap.shorten(title, width=511, placeholder='...'), date=date, severity=self.convert_severity(bugcrowd_severity), description=description, mitigation=mitigation, steps_to_reproduce=steps_to_reproduce, active=self.is_active(bugcrowd_state), verified=self.is_verified(bugcrowd_state), false_p=self.is_false_p(bugcrowd_state), out_of_scope=self.is_out_of_scope(bugcrowd_state), is_mitigated=self.is_mitigated(bugcrowd_state), static_finding=False, dynamic_finding=True, unique_id_from_tool=unique_id_from_tool, references=links)
            if self.is_not_applicable(bugcrowd_state):
                finding.active = False
                finding.severity = 'Info'
            if bug_endpoint:
                try:
                    bug_endpoint.clean()
                    try:
                        finding.unsaved_endpoints = [bug_endpoint]
                    except Exception as e:
                        logger.error('%s bug url from bugcrowd failed to parse to endpoint, error= %s', bug_endpoint, e)
                except ValidationError:
                    logger.error(f'Broken Bugcrowd endpoint {bug_endpoint.host} was skipped.')
            findings.append(finding)
        return findings

    def get_created_date(self, date):
        'Get the date of when a finding was created'
        return self.convert_log_timestamp(date)

    def get_latest_update_date(self, log):
        'Get the date of the last time a finding was updated'
        last_index = (len(log) - 1)
        entry = log[last_index]
        return self.convert_log_timestamp(entry['timestamp'])

    def include_finding(self, entry):
        'Determine whether this finding should be imported to DefectDojo'
        allowed_states = ['new', 'out_of_scope', 'not_applicable', 'not_reproducible', 'triaged', 'unresolved', 'resolved', 'informational']
        if (entry['attributes']['state'] in allowed_states):
            return True
        msg = '{} not in allowed bugcrowd submission states'.format(entry['attributes']['state'])
        raise ValueError(msg)

    def convert_log_timestamp(self, timestamp):
        "Convert a log entry's timestamp to a DefectDojo date"
        date_obj = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        return date_obj.strftime('%Y-%m-%d')

    def convert_severity(self, bugcrowd_severity):
        'Convert severity value'
        if (bugcrowd_severity == 5):
            return 'Info'
        if (bugcrowd_severity == 4):
            return 'Low'
        if (bugcrowd_severity == 3):
            return 'Medium'
        if (bugcrowd_severity == 2):
            return 'High'
        if (bugcrowd_severity == 1):
            return 'Critical'
        return 'Info'

    def is_active(self, bugcrowd_state):
        return ((bugcrowd_state == 'unresolved') or (not (self.is_mitigated(bugcrowd_state) or self.is_false_p(bugcrowd_state) or self.is_out_of_scope(bugcrowd_state) or (bugcrowd_state in {'not_reproducible', 'informational'}))))

    def is_duplicate(self, bugcrowd_state):
        return (bugcrowd_state == 'duplicate')

    def is_false_p(self, bugcrowd_state):
        return (bugcrowd_state == 'not_reproducible')

    def is_mitigated(self, bugcrowd_state):
        return (bugcrowd_state == 'resolved')

    def is_out_of_scope(self, bugcrowd_state):
        return (bugcrowd_state == 'out_of_scope')

    def is_not_applicable(self, bugcrowd_state):
        return (bugcrowd_state == 'not_applicable')

    def is_verified(self, bugcrowd_state):
        return ((bugcrowd_state == 'triaged') or (bugcrowd_state not in {'new', 'triaging'}))
