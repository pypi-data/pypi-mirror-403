import logging
import cvss.parser
from cvss.cvss2 import CVSS2
from cvss.cvss3 import CVSS3
from cvss.cvss4 import CVSS4
import datetime
from .models import Finding, Endpoint, Test

logger = logging.getLogger(__name__)

def parse_cvss_data(cvss_vector_string: str) -> dict:
    if not cvss_vector_string:
        return {}

    try:
        vectors = cvss.parser.parse_cvss_from_text(cvss_vector_string)
    except Exception as e:
        logger.debug("Failed to parse CVSS vector: %s", e)
        return {}

    if len(vectors) > 0:
        vector = vectors[0]
        major_version = cvssv2 = cvssv2_score = cvssv3 = cvssv3_score = cvssv4 = cvssv4_score = severity = None
        
        if isinstance(vector, CVSS4):
            major_version = 4
            cvssv4 = vector.clean_vector()
            cvssv4_score = vector.scores()[0]
            severity = vector.severities()[0]
        elif isinstance(vector, CVSS3):
            major_version = 3
            cvssv3 = vector.clean_vector()
            cvssv3_score = vector.scores()[2]
            severity = vector.severities()[0]
        elif isinstance(vector, CVSS2):
            major_version = 2
            cvssv2 = vector.clean_vector()
            cvssv2_score = vector.scores()[2]
            severity = vector.severities()[0]

        return {
            "major_version": major_version,
            "cvssv2": cvssv2,
            "cvssv2_score": cvssv2_score,
            "cvssv3": cvssv3,
            "cvssv3_score": cvssv3_score,
            "cvssv4": cvssv4,
            "cvssv4_score": cvssv4_score,
            "severity": severity,
        }
    return {}

def add_language(test, language, *args, **kwargs):
    pass

def get_npm_cwe(finding):
    return 0

def clean_tags(tags):
    return tags

def prepare_for_view(text):
    return text

def get_system_setting(name, default=None):
    return default

def create_notification(*args, **kwargs):
    pass

def serialize_finding(obj):
    if isinstance(obj, Finding):
        return obj.__dict__
    elif isinstance(obj, Endpoint):
        return obj.__dict__
    elif isinstance(obj, Test):
        return obj.__dict__
    elif isinstance(obj, Test.Engagement):
        return obj.__dict__
    elif obj.__class__.__name__ == "dict_values":
        return list(obj)
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
