# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import logging
import re
from norm_findings.stubs.django.utils.translation import gettext as _
from norm_findings.parsers.sarif.parser import SarifParser, get_codeFlowsDescription, get_snippet
logger = logging.getLogger(__name__)
CWE_REGEX = 'cwe-\\d+'

class MayhemParser(SarifParser):
    '\n    Mayhem SARIF Parser\n\n    This class extends the existing SARIF parser, but with some minor\n    modifications to better support the structure of Mayhem SARIF reports.\n    '

    def get_scan_types(self):
        return ['Mayhem SARIF Report']

    def get_description_for_scan_types(self, scan_type):
        return 'Mayhem SARIF reports from code or API runs.'

    def get_finding_type(self):
        'Mayhem findings are dynamic, not static'
        return (False, True)

    def get_finding_title(self, result, rule, location):
        'Get and clean the title text for Mayhem SARIF reports.'
        title = super().get_finding_title(result, rule, location)
        if (not title):
            return ''
        link_regex = '\\[[^\\]]{1,100}?\\]\\([^)]{1,200}?\\)'
        title = re.sub(link_regex, '', title)
        url_encoding_regex = '&#x\\d+;'
        title = re.sub(url_encoding_regex, '', title)
        quotes_regex = '[\\"\']'
        title = re.sub(quotes_regex, '', title)
        tdid_regex = 'TDID-\\d+\\s*-\\s*|TDID-\\d+-'
        title = re.sub(tdid_regex, '', title)
        return title.strip()

    def get_finding_description(self, result, rule, location):
        'Custom description formatting for Mayhem SARIF reports with markdown support'
        description = ''
        message = ''
        if ('message' in result):
            message = self._get_message_from_multiformatMessageString(result['message'], rule)
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
                shortDescription = self._get_message_from_multiformatMessageString(rule['shortDescription'], rule)
                if (shortDescription != message):
                    description += f'''**{_('Rule short description')}:** {shortDescription}
'''
            if ('fullDescription' in rule):
                fullDescription = self._get_message_from_multiformatMessageString(rule['fullDescription'], rule)
                if (fullDescription not in {message, shortDescription}):
                    description += f'''**{_('Rule full description')}:** {fullDescription}
'''
        if ('markdown' in result['message']):
            markdown = self._get_message_from_multiformatMessageString(result['message'], rule, content_type='markdown')
            markdown = markdown.replace('Details', 'Link')
            description += f'''**{_('Additional Details')}:**
{markdown}
'''
            description += "_(Unprintable characters are replaced with '?'; please see Mayhem for full reproducer.)_"
        if (len(result.get('codeFlows', [])) > 0):
            description += get_codeFlowsDescription(result['codeFlows'])
        return description.removesuffix('\n')

    def _get_message_from_multiformatMessageString(self, data, rule, content_type='text'):
        '\n        Get a message from multimessage struct\n\n        Differs from Sarif implementation in that it handles markdown, specifies content_type\n        '
        if ((content_type == 'markdown') and ('markdown' in data)):
            markdown = data.get('markdown')
            heading_regex = '^#+\\s*'
            markdown = re.sub(heading_regex, '', markdown, flags=re.MULTILINE)
            non_unicode_regex = '[^\\x09\\x0A\\x0D\\x20-\\x7E]'
            markdown = re.sub(non_unicode_regex, '?', markdown)
            return markdown.strip()
        if ((content_type == 'text') and ('text' in data)):
            text = data.get('text')
            if ((rule is not None) and ('id' in data)):
                text = rule['messageStrings'][data['id']].get('text')
                arguments = data.get('arguments', [])
                for i in range(6):
                    substitution_str = (('{' + str(i)) + '}')
                    if ((substitution_str in text) and (i < len(arguments))):
                        text = text.replace(substitution_str, arguments[i])
            return text
        return ''
