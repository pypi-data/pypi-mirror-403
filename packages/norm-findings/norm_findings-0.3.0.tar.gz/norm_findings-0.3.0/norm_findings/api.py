import os
import json
import importlib
import importlib.util
from pathlib import Path
from norm_findings.stubs.models import Test
from norm_findings.stubs.utils import serialize_finding

def parse_findings(parser_name: str, input_file: str, test_label: str = None, output_file: str = None) -> list:
    """
    Standard function to receive parser name and input/output file names, and return bindings.
    """
    # 1. Load the parser mapping to find the file
    mapping_path = os.path.join(os.path.dirname(__file__), "parser_mapping.json")
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            mapping = json.load(f)
    else:
        mapping = {}

    # 2. Determine module path and class name
    # Trim 'Parser' suffix if provided to standardize key lookup
    parser_key = parser_name[:-6] if parser_name.endswith('Parser') else parser_name
    
    parser_path = None
    if parser_name in mapping:
         parser_path = mapping[parser_name]
    elif parser_key in mapping:
         parser_path = mapping[parser_key]
    
    # Calculate module name
    base_module_name = f"norm_findings.parsers.{parser_key.lower()}.parser"

    # 3. Load the module
    try:
        module = importlib.import_module(base_module_name)
    except ImportError:
        if not parser_path:
             # Try conventional path
             parser_path = os.path.join(os.path.dirname(__file__), "parsers", parser_key.lower(), "parser.py")
        
        if os.path.exists(parser_path):
            spec = importlib.util.spec_from_file_location(base_module_name, os.path.abspath(parser_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            raise ValueError(f"Could not find parser: {parser_name}")

    # 4. Instantiate parser
    # Try finding the class name with or without 'Parser' suffix
    ParserClass = None
    target_name = f"{parser_key}Parser".lower()
    
    # 1. Exact or case-insensitive match
    for attr in dir(module):
        if attr.lower() == target_name:
            obj = getattr(module, attr)
            if isinstance(obj, type):
                ParserClass = obj
                break
    
    if not ParserClass:
        # 2. Fallback: Try exact match for parser_name (e.g. some classes don't have 'Parser' suffix?)
        if hasattr(module, parser_name):
             ParserClass = getattr(module, parser_name)

    if not ParserClass:
        # 3. Last resort: find first class ending in 'Parser' (Risky, but legacy behavior)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and attr.endswith('Parser'):
                ParserClass = obj
                break
    
    if not ParserClass:
        raise ValueError(f"Could not find parser class for: {parser_name}")

    parser_instance = ParserClass()

    # 5. Prepare test object
    test_obj = Test(product=test_label or "Standardized Parse")

    # 6. Call get_findings with standardized signature
    # Open in binary mode ('rb') for broad compatibility (zip, xml, json)
    with open(input_file, 'rb') as f:
        findings = parser_instance.get_findings(f, test_obj)

    # 7. Convert findings to list if it is a generator or None
    if findings is not None:
        findings = list(findings)
    else:
        findings = []

    # 8. Optionally write to output file
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(findings, f, indent=4, default=serialize_finding)

    return findings
