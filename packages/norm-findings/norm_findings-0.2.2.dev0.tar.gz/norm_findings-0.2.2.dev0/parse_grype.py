
#from dojo.models import Finding
from dojo.tools.anchore_grype.parser import AnchoreGrypeParser


parser = AnchoreGrypeParser()
with open("grype.json") as file:
    findings = parser.get_findings(file, "test")
    for finding in findings:
        print(finding)