# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from datetime import datetime
from html2text import html2text
from norm_findings.stubs.models import Finding

class MobSFapireport():

    def get_findings(self, scan_file, test):
        dupes = {}
        find_date = datetime.now()
        test_description = ''
        if ('name' in scan_file):
            test_description = '**Info:**\n'
            if ('packagename' in scan_file):
                test_description = '{}  **Package Name:** {}\n'.format(test_description, scan_file['packagename'])
            if ('mainactivity' in scan_file):
                test_description = '{}  **Main Activity:** {}\n'.format(test_description, scan_file['mainactivity'])
            if ('pltfm' in scan_file):
                test_description = '{}  **Platform:** {}\n'.format(test_description, scan_file['pltfm'])
            if ('sdk' in scan_file):
                test_description = '{}  **SDK:** {}\n'.format(test_description, scan_file['sdk'])
            if ('min' in scan_file):
                test_description = '{}  **Min SDK:** {}\n'.format(test_description, scan_file['min'])
            if ('targetsdk' in scan_file):
                test_description = '{}  **Target SDK:** {}\n'.format(test_description, scan_file['targetsdk'])
            if ('minsdk' in scan_file):
                test_description = '{}  **Min SDK:** {}\n'.format(test_description, scan_file['minsdk'])
            if ('maxsdk' in scan_file):
                test_description = '{}  **Max SDK:** {}\n'.format(test_description, scan_file['maxsdk'])
            test_description = f'''{test_description}
**File Information:**
'''
            if ('name' in scan_file):
                test_description = '{}  **Name:** {}\n'.format(test_description, scan_file['name'])
            if ('md5' in scan_file):
                test_description = '{}  **MD5:** {}\n'.format(test_description, scan_file['md5'])
            if ('sha1' in scan_file):
                test_description = '{}  **SHA-1:** {}\n'.format(test_description, scan_file['sha1'])
            if ('sha256' in scan_file):
                test_description = '{}  **SHA-256:** {}\n'.format(test_description, scan_file['sha256'])
            if ('size' in scan_file):
                test_description = '{}  **Size:** {}\n'.format(test_description, scan_file['size'])
            if ('urls' in scan_file):
                curl = ''
                for url in scan_file['urls']:
                    for durl in url['urls']:
                        curl = f'''{durl}
'''
                if curl:
                    test_description = f'''{test_description}
**URL's:**
 {curl}
'''
            if ('bin_anal' in scan_file):
                test_description = '{}  \n**Binary Analysis:** {}\n'.format(test_description, scan_file['bin_anal'])
        test.description = html2text(test_description)
        mobsf_findings = []
        if ('permissions' in scan_file):
            if isinstance(scan_file['permissions'], list):
                for details in scan_file['permissions']:
                    mobsf_item = {'category': 'Mobile Permissions', 'title': details.get('name', ''), 'severity': self.getSeverityForPermission(details.get('status')), 'description': ((((((('**Permission Type:** ' + details.get('name', '')) + ' (') + details.get('status', '')) + ')\n\n**Description:** ') + details.get('description', '')) + '\n\n**Reason:** ') + details.get('reason', '')), 'file_path': None}
                    mobsf_findings.append(mobsf_item)
            else:
                for (permission, details) in list(scan_file['permissions'].items()):
                    mobsf_item = {'category': 'Mobile Permissions', 'title': permission, 'severity': self.getSeverityForPermission(details.get('status', '')), 'description': ((('**Permission Type:** ' + permission) + '\n\n**Description:** ') + details.get('description', '')), 'file_path': None}
                    mobsf_findings.append(mobsf_item)
        if ('insecure_connections' in scan_file):
            for details in scan_file['insecure_connections']:
                insecure_urls = ''
                for url in details.split(','):
                    insecure_urls = ((insecure_urls + url) + '\n')
                mobsf_item = {'category': None, 'title': 'Insecure Connections', 'severity': 'Low', 'description': insecure_urls, 'file_path': None}
                mobsf_findings.append(mobsf_item)
        if ('certificate_analysis' in scan_file):
            if (scan_file['certificate_analysis'] != {}):
                certificate_info = scan_file['certificate_analysis']['certificate_info']
                for details in scan_file['certificate_analysis']['certificate_findings']:
                    if (len(details) == 3):
                        mobsf_item = {'category': 'Certificate Analysis', 'title': details[2], 'severity': details[0].title(), 'description': ((details[1] + '\n\n**Certificate Info:** ') + certificate_info), 'file_path': None}
                        mobsf_findings.append(mobsf_item)
                    elif (len(details) == 2):
                        mobsf_item = {'category': 'Certificate Analysis', 'title': details[1], 'severity': details[0].title(), 'description': ((details[1] + '\n\n**Certificate Info:** ') + certificate_info), 'file_path': None}
                        mobsf_findings.append(mobsf_item)
        if ('manifest_analysis' in scan_file):
            if ((scan_file['manifest_analysis'] != {}) and isinstance(scan_file['manifest_analysis'], dict)):
                if scan_file['manifest_analysis']['manifest_findings']:
                    for details in scan_file['manifest_analysis']['manifest_findings']:
                        mobsf_item = {'category': 'Manifest Analysis', 'title': details['title'], 'severity': details['severity'].title(), 'description': ((details['description'] + '\n\n ') + details['name']), 'file_path': None}
                        mobsf_findings.append(mobsf_item)
                else:
                    for details in scan_file['manifest_analysis']:
                        mobsf_item = {'category': 'Manifest Analysis', 'title': details['title'], 'severity': details['stat'].title(), 'description': ((details['desc'] + '\n\n ') + details['name']), 'file_path': None}
                        mobsf_findings.append(mobsf_item)
        if ('code_analysis' in scan_file):
            if (scan_file['code_analysis'] != {}):
                if scan_file['code_analysis'].get('findings'):
                    for details in scan_file['code_analysis']['findings']:
                        metadata = scan_file['code_analysis']['findings'][details]
                        mobsf_item = {'category': 'Code Analysis', 'title': details, 'severity': metadata['metadata']['severity'].title(), 'description': metadata['metadata']['description'], 'file_path': None}
                        mobsf_findings.append(mobsf_item)
                else:
                    for details in scan_file['code_analysis']:
                        metadata = scan_file['code_analysis'][details]
                        if metadata.get('metadata'):
                            mobsf_item = {'category': 'Code Analysis', 'title': details, 'severity': metadata['metadata']['severity'].title(), 'description': metadata['metadata']['description'], 'file_path': None}
                            mobsf_findings.append(mobsf_item)
        if ('binary_analysis' in scan_file):
            if isinstance(scan_file['binary_analysis'], list):
                for details in scan_file['binary_analysis']:
                    for binary_analysis_type in details:
                        if (binary_analysis_type != 'name'):
                            mobsf_item = {'category': 'Binary Analysis', 'title': details[binary_analysis_type]['description'].split('.')[0], 'severity': details[binary_analysis_type]['severity'].title(), 'description': details[binary_analysis_type]['description'], 'file_path': details['name']}
                            mobsf_findings.append(mobsf_item)
            elif scan_file['binary_analysis'].get('findings'):
                for details in scan_file['binary_analysis']['findings'].values():
                    mobsf_item = {'category': 'Binary Analysis', 'title': details['detailed_desc'], 'severity': details['severity'].title(), 'description': details['detailed_desc'], 'file_path': None}
                    mobsf_findings.append(mobsf_item)
            else:
                for details in scan_file['binary_analysis'].values():
                    mobsf_item = {'category': 'Binary Analysis', 'title': details['detailed_desc'], 'severity': details['severity'].title(), 'description': details['detailed_desc'], 'file_path': None}
                    mobsf_findings.append(mobsf_item)
        if ('android_api' in scan_file):
            for (api, details) in list(scan_file['android_api'].items()):
                mobsf_item = {'category': 'Android API', 'title': details['metadata']['description'], 'severity': details['metadata']['severity'].title(), 'description': ((('**API:** ' + api) + '\n\n**Description:** ') + details['metadata']['description']), 'file_path': None}
                mobsf_findings.append(mobsf_item)
        if ('manifest' in scan_file):
            for details in scan_file['manifest']:
                mobsf_item = {'category': 'Manifest', 'title': details['title'], 'severity': details['stat'], 'description': details['desc'], 'file_path': None}
                mobsf_findings.append(mobsf_item)
        if ('findings' in scan_file):
            for (title, finding) in list(scan_file['findings'].items()):
                description = title
                file_path = None
                if ('path' in finding):
                    description += '\n\n**Files:**\n'
                    for path in finding['path']:
                        if (file_path is None):
                            file_path = path
                        description = (((description + ' * ') + path) + '\n')
                mobsf_item = {'category': 'Findings', 'title': title, 'severity': finding['level'], 'description': description, 'file_path': file_path}
                mobsf_findings.append(mobsf_item)
        if isinstance(scan_file, list):
            for finding in scan_file:
                mobsf_item = {'category': finding['category'], 'title': finding['name'], 'severity': finding['severity'], 'description': ((((((finding['description'] + '\n') + '**apk_exploit_dict:** ') + str(finding['apk_exploit_dict'])) + '\n') + '**line_number:** ') + str(finding['line_number'])), 'file_path': finding['file_object']}
                mobsf_findings.append(mobsf_item)
        for mobsf_finding in mobsf_findings:
            title = mobsf_finding['title']
            sev = self.getCriticalityRating(mobsf_finding['severity'])
            description = ''
            file_path = None
            if mobsf_finding['category']:
                description += (('**Category:** ' + mobsf_finding['category']) + '\n\n')
            description += html2text(mobsf_finding['description'])
            finding = Finding(title=title, cwe=919, test=test, description=description, severity=sev, references=None, date=find_date, static_finding=True, dynamic_finding=False, nb_occurences=1)
            if mobsf_finding['file_path']:
                finding.file_path = mobsf_finding['file_path']
                dupe_key = (((sev + title) + description) + mobsf_finding['file_path'])
            else:
                dupe_key = ((sev + title) + description)
            if mobsf_finding['category']:
                dupe_key += mobsf_finding['category']
            if (dupe_key in dupes):
                find = dupes[dupe_key]
                if (description is not None):
                    find.description += description
                find.nb_occurences += 1
            else:
                dupes[dupe_key] = finding
        return list(dupes.values())

    def getSeverityForPermission(self, status):
        "\n        Convert status for permission detection to severity\n\n        In MobSF there is only 4 know values for permission,\n         we map them as this:\n        dangerous         => High (Critical?)\n        normal            => Info\n        signature         => Info (it's positive so... Info)\n        signatureOrSystem => Info (it's positive so... Info)\n        "
        if (status == 'dangerous'):
            return 'High'
        return 'Info'

    def getCriticalityRating(self, rating):
        criticality = 'Info'
        if (rating.lower() == 'good'):
            criticality = 'Info'
        elif (rating.lower() == 'warning'):
            criticality = 'Low'
        elif (rating.lower() == 'vulnerability'):
            criticality = 'Medium'
        else:
            criticality = rating.lower().capitalize()
        return criticality

    def suite_data(self, suites):
        suite_info = ''
        suite_info += (suites['name'] + '\n')
        suite_info += (('Cipher Strength: ' + str(suites['cipherStrength'])) + '\n')
        if ('ecdhBits' in suites):
            suite_info += (('ecdhBits: ' + str(suites['ecdhBits'])) + '\n')
        if ('ecdhStrength' in suites):
            suite_info += ('ecdhStrength: ' + str(suites['ecdhStrength']))
        suite_info += '\n\n'
        return suite_info
