# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Finding

from norm_findings.stubs.models import Finding

class DeepfenceThreatmapperSecret():

    def get_findings(self, scan_file, test):
        if (('Name' in test) and ('Signature' in test)):
            return self._parse_old_format(scan_file, test, test)
        if (('Content Starting Index' in test) and ('Masked' in test)):
            return self._parse_new_format(scan_file, test, test)
        return None

    def _parse_old_format(self, row, headers, test):
        description = ''
        Filename = row[headers['Filename']]
        Content = row[headers['Content']]
        Name = row[headers['Name']]
        Rule = row[headers['Rule']]
        Severity = row[headers['Severity']]
        Node_Name = row[headers['Node Name']]
        Container_Name = row[headers['Container Name']]
        Kubernetes_Cluster_Name = row[headers['Kubernetes Cluster Name']]
        Signature = row[headers['Signature']]
        description += f'''**Filename:** {Filename}
'''
        description += f'''**Name:** {Name}
'''
        description += f'''**Rule:** {Rule}
'''
        description += f'''**Node Name:** {Node_Name}
'''
        description += f'''**Container Name:** {Container_Name}
'''
        description += f'''**Kubernetes Cluster Name:** {Kubernetes_Cluster_Name}
'''
        description += f'''**Content:** {Content}
'''
        description += f'''**Signature:** {Signature}
'''
        if (Name and Severity):
            return Finding(title=str(Name), description=description, file_path=Filename, severity=self.severity(Severity), static_finding=False, dynamic_finding=True, test=test)
        return None

    def _parse_new_format(self, row, headers, test):
        description = ''
        Filename = row[headers['Filename']]
        Content = row[headers['Content']]
        Rule = row[headers['Rule']]
        Severity = row[headers['Severity']]
        Content_Starting_Index = row[headers['Content Starting Index']]
        Node_Name = row[headers['Node Name']]
        Node_Type = row[headers['Node Type']]
        Kubernetes_Cluster_Name = row[headers['Kubernetes Cluster Name']]
        Masked = row[headers['Masked']]
        description += f'''**Filename:** {Filename}
'''
        description += f'''**Rule:** {Rule}
'''
        description += f'''**Node Name:** {Node_Name}
'''
        description += f'''**Node Type:** {Node_Type}
'''
        description += f'''**Kubernetes Cluster Name:** {Kubernetes_Cluster_Name}
'''
        description += f'''**Content:** {Content}
'''
        description += f'''**Content Starting Index:** {Content_Starting_Index}
'''
        description += f'''**Masked:** {Masked}
'''
        title = (f'{Rule} in {Filename}' if Rule else 'Secret Finding')
        if Severity:
            return Finding(title=title, description=description, file_path=Filename, severity=self.severity(Severity), static_finding=False, dynamic_finding=True, test=test)
        return None

    def severity(self, severity_input):
        if (severity_input is None):
            return 'Info'
        return severity_input.capitalize()
