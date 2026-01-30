# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: Endpoint, Finding

import json
from datetime import datetime
from dateutil import parser as date_parser
from norm_findings.stubs.models import Endpoint, Finding
from norm_findings.stubs.utils import parse_cvss_data

class AWSInspector2Parser():
    'Import AWS Inspector2 json.'

    def get_scan_types(self):
        return ['AWS Inspector2 Scan']

    def get_label_for_scan_types(self, scan_type):
        return 'AWS Inspector2 Scan'

    def get_description_for_scan_types(self, scan_type):
        return 'AWS Inspector2 report file can be imported in JSON format (aws inspector2 list-findings).'

    def get_findings(self, scan_file, test):
        tree = json.load(scan_file)
        raw_findings = tree.get('findings', None)
        if (not isinstance(raw_findings, list)):
            msg = 'Incorrect Inspector2 report format'
            raise TypeError(msg)
        self.test = test
        findings = []
        for raw_finding in raw_findings:
            finding = self.get_base_finding(raw_finding)
            finding_type = raw_finding.get('type', None)
            if (finding_type == 'PACKAGE_VULNERABILITY'):
                finding = self.get_package_vulnerability(finding, raw_finding)
            elif (finding_type == 'CODE_VULNERABILITY'):
                finding = self.get_code_vulnerability(finding, raw_finding)
            elif (finding_type == 'NETWORK_REACHABILITY'):
                finding = self.get_network_reachability(finding, raw_finding)
            else:
                msg = 'Incorrect Inspector2 report format'
                raise TypeError(msg)
            finding = self.get_cvss_details(finding, raw_finding)
            finding = self.process_endpoints(finding, raw_finding)
            findings.append(finding)
        return findings

    def get_severity(self, severity_string):
        if (severity_string == 'UNTRIAGED'):
            severity_string = 'Info'
        return severity_string.title()

    def get_base_finding(self, raw_finding: dict) -> Finding:
        finding_id = raw_finding.get('findingArn')
        title = raw_finding.get('title', 'The title could not be identified...')
        description = ''
        if ((aws_account := raw_finding.get('awsAccountId')) is not None):
            description += f'''**AWS Account**: {aws_account}
'''
        if (finding_id is not None):
            description += f'''**Finding ARN**: {finding_id}
'''
        if ((inspector_score := raw_finding.get('inspectorScore')) is not None):
            description += f'''Inspector score: {inspector_score}
'''
        if ((discovered_at := raw_finding.get('firstObservedAt')) is not None):
            description += f'''Discovered at: {discovered_at}
'''
        if ((last_seen_at := raw_finding.get('lastObservedAt')) is not None):
            description += f'''Last seen: {last_seen_at}
'''
        if ((orig_description := raw_finding.get('description')) is not None):
            description += f'''Original description: 
{orig_description}
'''
        finding = Finding(title=title, test=self.test, description=description, severity=self.get_severity(raw_finding.get('severity', 'Info')), unique_id_from_tool=finding_id, static_finding=True, dynamic_finding=False)
        if (raw_finding.get('status', 'ACTIVE') == 'ACTIVE'):
            mitigated = None
            is_mitigated = False
            active = True
        else:
            is_mitigated = True
            active = False
            if ((last_observed := raw_finding.get('lastObservedAt')) is not None):
                mitigated = date_parser.parse(last_observed)
            else:
                mitigated = datetime.now(datetime.timezone.utc)
        finding.active = active
        finding.is_mitigated = is_mitigated
        finding.mitigated = mitigated
        finding.epss_score = raw_finding.get('epss', {}).get('score', None)
        return finding

    def get_cvss_details(self, finding: Finding, raw_finding: dict) -> Finding:
        cvss_details = raw_finding.get('inspectorScoreDetails', {}).get('adjustedCvss', {})
        if (cvss_vector := cvss_details.get('scoringVector')):
            if (cvss_data := parse_cvss_data(cvss_vector)):
                finding.cvssv2 = cvss_data.get('cvssv2')
                finding.cvssv3 = cvss_data.get('cvssv3')
                finding.cvssv4 = cvss_data.get('cvssv4')
        return finding

    def get_package_vulnerability(self, finding: Finding, raw_finding: dict) -> Finding:
        vulnerability_details = raw_finding.get('packageVulnerabilityDetails', {})
        vulnerability_packages_descriptions = '\n'.join([f'''*Vulnerable package*: {vulnerability_package.get('name', 'N/A')}
	package manager: {vulnerability_package.get('packageManager', 'N/A')}
	version: {vulnerability_package.get('version', 'N/A')}
	fixed version: {vulnerability_package.get('fixedInVersion', 'N/A')}
	remediation: {vulnerability_package.get('remediation', 'N/A')}
''' for vulnerability_package in vulnerability_details.get('vulnerablePackages', [])])
        if ((vulnerability_id := vulnerability_details.get('vulnerabilityId', None)) is not None):
            finding.unsaved_vulnerability_ids = [vulnerability_id]
        vulnerability_source = vulnerability_details.get('source')
        vulnerability_source_url = vulnerability_details.get('sourceUrl')
        if ((vulnerability_source is not None) and (vulnerability_source_url is not None)):
            finding.url = vulnerability_source_url
            finding.description += f'''
**Additional info**
Vulnerability info from: {vulnerability_source} {vulnerability_source_url}
Affected packages:
{vulnerability_packages_descriptions}
'''
        return finding

    def get_code_vulnerability(self, finding: Finding, raw_finding: dict) -> Finding:
        cwes = raw_finding.get('cwes', [])
        detector_id = raw_finding.get('detectorId', 'N/A')
        detector_name = raw_finding.get('detectorName', 'N/A')
        file_path_info = raw_finding.get('filePath', {})
        file_name = file_path_info.get('fileName', 'N/A')
        file_path = file_path_info.get('filePath', 'N/A')
        start_line = file_path_info.get('startLine', 'N/A')
        end_line = file_path_info.get('endLine', 'N/A')
        detector_tags = ', '.join(raw_finding.get('detectorTags', []))
        reference_urls = ', '.join(raw_finding.get('referenceUrls', []))
        rule_id = raw_finding.get('ruleId', 'N/A')
        layer_arn = raw_finding.get('sourceLambdaLayerArn', 'N/A')
        string_cwes = ', '.join(cwes)
        finding.cwe = (cwes[0] if cwes else None)
        finding.file_path = f'{file_path}{file_name}'
        finding.sast_source_file_path = f'{file_path}{file_name}'
        finding.line = start_line
        finding.sast_source_line = start_line
        finding.description += f'''
**Additional info**
CWEs: {string_cwes}
Vulnerability info from: {detector_id} {detector_name}
Rule: {rule_id}
Lines: {start_line} - {end_line}
Tags: {(detector_tags or 'N/A')}
URLs: {(reference_urls or 'N/A')}
Lambda layer ARN: {layer_arn}
'''
        return finding

    def get_network_reachability(self, finding: Finding, raw_finding: dict) -> Finding:
        network_path_info = raw_finding.get('networkPath', {})
        network_path_steps = network_path_info.get('steps', [])
        steps_descriptions = '\n'.join([f'''steps:
{step_number}: {step.get('componentId', 'N/A')} {step.get('componentType', 'N/A')}''' for (step_number, step) in enumerate(network_path_steps)])
        open_port_range_info = raw_finding.get('openPortRange', {})
        port_range_start = open_port_range_info.get('begin', 'N/A')
        port_range_end = open_port_range_info.get('end', 'N/A')
        protocol = raw_finding.get('protocol', 'N/A')
        finding.description += f'''
**Additional info**
protocol {protocol}, port range {port_range_start} - {port_range_end}{steps_descriptions}
'''
        return finding

    def process_endpoints(self, finding: Finding, raw_finding: dict) -> Finding:
        impact = []
        endpoints = []
        for resource_info in raw_finding.get('resources', {}):
            resource_type = resource_info.get('type', None)
            resource_id = resource_info.get('id', 'N/A')
            resource_details = resource_info.get('details', {})
            endpoint_host = f'{resource_type}_{resource_id}'.replace(':', '_').replace('/', '_')
            if (resource_type == 'AWS_EC2_INSTANCE'):
                aws_account = raw_finding.get('awsAccountId')
                resource_region = resource_info.get('region', 'N/A')
                endpoint_host = resource_id
                ec2_instance_details = resource_details.get('awsEc2Instance', None)
                if ec2_instance_details:
                    impact.extend((f'ARN: {resource_id}', f"Image ID: {ec2_instance_details.get('imageId', 'N/A')}", f"IPv4 address: {ec2_instance_details.get('ipV4Addresses', 'N/A')}", f"Subnet: {ec2_instance_details.get('subnetId', 'N/A')}", f"VPC: {ec2_instance_details.get('vpcId', 'N/A')}", f'Region: {resource_region}', f'AWS Account: {aws_account}', f"Launched at: {ec2_instance_details.get('launchedAt', 'N/A')}", '---'))
            elif (resource_type == 'AWS_ECR_CONTAINER_IMAGE'):
                image_id = resource_id.split('repository/')[1].replace('sha256:', '').replace('/', '-')
                endpoint_host = image_id
                ecr_image_details = resource_details.get('awsEcrContainerImage', None)
                if ecr_image_details:
                    impact.extend((f'ARN: {resource_id}', f"Registry: {ecr_image_details.get('registry', 'N/A')}", f"Repository: {ecr_image_details.get('repositoryName', 'N/A')}", f"Hash: {ecr_image_details.get('imageHash', 'N/A')}", f"Author: {ecr_image_details.get('author', 'N/A')}", f"Pushed at: {ecr_image_details.get('pushedAt', 'N/A')}", f"Image tags: {','.join(ecr_image_details.get('imageTags', []))}", '---'))
            elif (resource_type == 'AWS_ECR_REPOSITORY'):
                pass
            elif (resource_type == 'AWS_LAMBDA_FUNCTION'):
                lambda_id = resource_id.split('function:')[1].replace(':', '-').replace('/', '-')
                endpoint_host = lambda_id
                lambda_details = resource_details.get('awsLambdaFunction', None)
                if lambda_details:
                    impact.extend((f'ARN: {resource_id}', f"Name: {lambda_details.get('functionName', 'N/A')}", f"Version: {lambda_details.get('version', 'N/A')}", f"Runtime: {lambda_details.get('runtime', 'N/A')}", f"Hash: {lambda_details.get('codeSha256', 'N/A')}", f"Pushed at: {lambda_details.get('lastModifiedAt', 'N/A')}"))
            else:
                msg = 'Incorrect Inspector2 report format'
                raise TypeError(msg)
            endpoints.append(Endpoint(host=endpoint_host))
        finding.impact = '\n'.join(impact)
        finding.unsaved_endpoints = []
        finding.unsaved_endpoints.extend(endpoints)
        return finding
