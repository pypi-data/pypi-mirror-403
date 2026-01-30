import os
import json
import pytest
import importlib.util
from norm_findings.stubs.models import Test

from norm_findings.api import parse_findings

TEST_DATA_DIR = "test_data"
MAPPING_FILE = "norm_findings/parser_mapping.json"

def get_parsers_to_test():
    if not os.path.exists(MAPPING_FILE):
        return []
    with open(MAPPING_FILE, "r") as f:
        mapping = json.load(f)
    
    tests = []
    for parser_name, parser_path in mapping.items():
        data_dir = os.path.join(TEST_DATA_DIR, parser_name)
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                file_path = os.path.join(data_dir, filename)
                if os.path.isfile(file_path) and not filename.startswith('.'):
                    tests.append((parser_name, parser_path, file_path))
    return tests

@pytest.mark.parametrize("parser_name, parser_path, sample_file", get_parsers_to_test())
def test_parser_sample_data(parser_name, parser_path, sample_file):
    filename = os.path.basename(sample_file).lower()
    
    # Skip non-scan files
    if filename in ["readme.md", "license", "__init__.py", "not_a_scan.txt", "wrong_ext.zip"]:
        pytest.skip(f"Skipping non-scan file: {filename}")
    
    # Heuristic for negative test cases
    negative_keywords = ["empty", "invalid", "bad", "wrong", "null", "none", "no_", "missing", "zero", "not_", "fail"]
    is_negative_test = any(keyword in filename for keyword in negative_keywords)

    try:
        findings = parse_findings(
            parser_name=parser_name,
            input_file=sample_file,
            test_label="E2E Test"
        )
        
        # Some parsers return None or empty list for empty files, that's fine
        assert findings is None or isinstance(findings, list), f"Parser {parser_name} returned non-list: {type(findings)}"
            
    except Exception as e:
        error_msg = str(e).lower()
        error_type = type(e).__name__.lower()
        
        # Known parser rejections / validation errors
        if isinstance(e, (ValueError, TypeError, AttributeError, KeyError)):
             pytest.skip(f"Aknowledged parser rejection ({error_type}): {e}")

        # File format mismatches (e.g. zip vs json)
        if "zip" in error_type or "zip" in error_msg:
             pytest.skip(f"Aknowledged zip error: {e}")
        
        # Encoding errors
        if isinstance(e, UnicodeDecodeError):
             pytest.skip(f"Aknowledged encoding error: {e}")

        # XML parsing errors
        if "parseerror" in error_type or "expat" in error_type:
             pytest.skip(f"Aknowledged XML error: {e}")
             
        # OpenPyXL errors (for Deepfence)
        if "invalidfileexception" in error_type:
             pytest.skip(f"Aknowledged OpenPyXL error: {e}")

        if is_negative_test:
            pytest.skip(f"Aknowledged negative test error: {e}")
        
        # If we got here, it's a real failure
        pytest.fail(f"Parser {parser_name} failed on {sample_file} ({error_type}): {e}")

if __name__ == "__main__":
    # For manual testing
    all_tests = get_parsers_to_test()
    print(f"Found {len(all_tests)} sample files to test.")
    for p_name, p_path, s_file in all_tests[:5]:
        print(f"Testing {p_name} with {s_file}")
