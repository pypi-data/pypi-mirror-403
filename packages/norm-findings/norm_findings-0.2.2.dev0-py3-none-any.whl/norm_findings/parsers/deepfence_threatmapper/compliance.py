# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from norm_findings.stubs.models import Finding

class DeepfenceThreatmapperCompliance():

    def get_findings(self, scan_file, test):
        if (('compliance_check_type' in test) and ('test_number' in test)):
            return self._parse_old_format(scan_file, test, test)
        if (('Compliance Standard' in test) and ('Control ID' in test)):
            return self._parse_new_format(scan_file, test, test)
        return None

    def _parse_old_format(self, row, headers, test):
        compliance_check_type = row[headers['compliance_check_type']]
        count = row[headers['count']]
        doc_id = row[headers['doc_id']]
        host_name = row[headers['host_name']]
        cloud_account_id = row[headers['cloud_account_id']]
        masked = row[headers['masked']]
        node_id = row[headers['node_id']]
        node_name = row[headers['node_name']]
        node_type = row[headers['node_type']]
        status = row[headers['status']]
        test_category = row[headers['test_category']]
        test_desc = row[headers['test_desc']]
        test_info = row[headers['test_info']]
        test_number = row[headers['test_number']]
        description = f'''**Compliance Check Type:** {compliance_check_type}
**Host Name:** {host_name}
**Cloud Account ID:** {cloud_account_id}
**Masked:** {masked}
**Node ID:** {node_id}
**Node Name:** {node_name}
**Node Type:** {node_type}
**Status:** {status}
**Test Category:** {test_category}
**Test Description:** {test_desc}
**Test Info:** {test_info}
**Test Number:** {test_number}
**Count:** {count}
**Doc ID:** {doc_id}
'''
        return Finding(title=f'Threatmapper_Compliance_Report-{test_number}', description=description, severity=self.compliance_severity(status), static_finding=False, dynamic_finding=True, test=test)

    def _parse_new_format(self, row, headers, test):
        compliance_standard = row[headers['Compliance Standard']]
        status = row[headers['Status']]
        category = row[headers['Category']]
        description_text = row[headers['Description']]
        info = row[headers['Info']]
        control_id = row[headers['Control ID']]
        node_name = row[headers['Node Name']]
        node_type = row[headers['Node Type']]
        remediation = row[headers['Remediation']]
        masked = row[headers['Masked']]
        description = f'''**Compliance Standard:** {compliance_standard}
**Status:** {status}
**Category:** {category}
**Description:** {description_text}
**Info:** {info}
**Control ID:** {control_id}
**Node Name:** {node_name}
**Node Type:** {node_type}
**Remediation:** {remediation}
**Masked:** {masked}
'''
        return Finding(title=f'Threatmapper_Compliance_Report-{control_id}', description=description, severity=self.compliance_severity(status), static_finding=False, dynamic_finding=True, mitigation=remediation, test=test)

    def compliance_severity(self, severity_input):
        if (severity_input is None):
            return 'Info'
        severity_input = severity_input.lower()
        if (severity_input in {'pass', 'info'}):
            return 'Info'
        if (severity_input == 'warn'):
            return 'Medium'
        if (severity_input == 'fail'):
            return 'High'
        return 'Info'
