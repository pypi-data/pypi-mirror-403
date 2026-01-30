# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import csv
import io
import logging
import zipfile
from pathlib import Path
logger = logging.getLogger(__name__)

class BlackduckCRImporter():
    "\n    Importer for blackduck. V3 is different in that it creates a Finding in defect dojo\n    for each vulnerable component version used in a project, for each license that is\n    In Violation for the components, AND for each license that is marked with a 'License Risk'\n    that is anything other than 'OK' as a For Review Finding in defect dojo.\n    Security Risks and License Risks.\n    Security Risks have the severity and impact of it's highest vulnerability the component has.\n    "

    def parse_findings(self, report: Path) -> (dict, dict, dict):
        '\n        Given a path to a zip file, this function will find the relevant CSV files and\n        return three dictionaries with the information needed. Dictionaries are components, source and\n        security risks.\n        :param report: Path to zip file\n        :return: ( {component_id:details} , {component_id:[vulns]}, {component_id:[source]} )\n        '
        if zipfile.is_zipfile(report):
            report.seek(0)
            return self._process_zipfile(report)
        msg = f'File {report} not a zip!'
        raise ValueError(msg)

    def _process_zipfile(self, report: Path) -> (dict, dict, dict):
        '\n        Open the zip file and extract information on vulnerable packages from security.csv,\n        as well as license risk information from components.csv, and location/context from source.csv.\n        :param report: the file\n        :return: (dict, dict, dict)\n        '
        components = {}
        source = {}
        try:
            with zipfile.ZipFile(report) as zipf:
                c_file = False
                s_file = False
                for full_file_name in zipf.namelist():
                    file_name = full_file_name.split('/')[(- 1)]
                    if ('component' in file_name):
                        with io.TextIOWrapper(zipf.open(full_file_name), encoding='utf-8') as f:
                            components = self.__get_components(f)
                            c_file = True
                    elif ('security' in file_name):
                        with io.TextIOWrapper(zipf.open(full_file_name), encoding='utf-8') as f:
                            security_issues = self.__get_security_risks(f)
                            s_file = True
                    elif ('source' in file_name):
                        with io.TextIOWrapper(zipf.open(full_file_name), encoding='utf-8') as f:
                            source = self.__get_source(f)
        except Exception:
            logger.exception('Could not process zip file')
            if (not (c_file and s_file)):
                msg = 'Zip file missing needed files!'
                raise Exception(msg)
        return (components, security_issues, source)

    def __get_source(self, src_file) -> dict:
        '\n        Builds a dictionary to reference source location data for components.\n        Each component is represented to match the component dictionary\n        {\n            "component_id:version_id":\n                {"column1":"value", "column2":"value", ...},\n            ...\n        }\n        Each row in the CSV will be a unique entry.\n        :param src_file: File object of the source.csv\n        :return: {str:dct}\n        '
        source = {}
        records = csv.DictReader(src_file)
        for record in records:
            source[(((record.get('Component id') + ':') + record.get('Version id')) + ':License')] = {x[0]: x[1] for x in record.items()}
        return source

    def __get_components(self, csv_file) -> dict:
        '\n        Builds a dictionary to reference components.\n        Each component is represented\n        {\n            "component_id:version_id":\n                {"column1":"value", "column2":"value", ...},\n            ...\n        }\n        Each row in the CSV will be a unique entry.\n        :param csv_file: File object of the component.csv\n        :return: {str:dict}\n        '
        components = {}
        records = csv.DictReader(csv_file)
        for record in records:
            components[(((record.get('Component id') + ':') + record.get('Version id')) + ':License')] = {x[0]: x[1] for x in record.items()}
        return components

    def __get_security_risks(self, csv_file) -> dict:
        '\n        Creates a dictionary to represent vulnerabilities in a given component. Each entry in the\n        dictionary is represented:\n        {\n            "component_id:version_id":\n                [{vuln_column1: value, vuln_column2: value, ...},{...}]\n        }\n        Each entry is a component with the id:version_id as a key, and a list of vulnerabilities\n        as the value.\n        :param csv_file:\n        :return: {component:[vulns]}\n        '
        securities = {}
        records = csv.DictReader(csv_file)
        for record in records:
            key = (((record.get('Component id') + ':') + record.get('Version id')) + ':security')
            vulns = (securities.get(key) or [])
            vulns.append({x[0]: x[1] for x in record.items()})
            securities[key] = vulns
        return securities
