import sys
import os
import importlib
import jsonargparse
from pathlib import Path
import datetime

try:
    import ujson as json_lib
except ImportError:
    import json as json_lib

# Internal imports
from norm_findings.stubs.models import Finding, Endpoint, Test
from norm_findings.stubs.utils import serialize_finding
from norm_findings.api import parse_findings


def create_parser(parsers):
    parser = jsonargparse.ArgumentParser(description="norm-findings - Security Finding Normalizer")

    convert_parser = jsonargparse.ArgumentParser('convert', description="Convert report to JSON findings")
    convert_parser.add_argument("--parser", choices=parsers, required=True, help="Parser to use")
    convert_parser.add_argument("--input-file", required=True, help="Input file to parse")
    convert_parser.add_argument("--output-file", required=True, help="Output file to write findings to")
    convert_parser.add_argument("--test", type=str, help="Populate the Findings test field")
    convert_parser.add_argument("--print", action="store_true", help="Print findings to console")

    server_parser = jsonargparse.ArgumentParser('server', description="Start conversion server")
    server_parser.add_argument("--port", type=int, default=8000)

    subs = parser.add_subcommands()
    subs.add_subcommand("convert", convert_parser)
    subs.add_subcommand("server", server_parser)

    return parser

def convert(args):
    parser_name = args['parser']
    input_file = args['input_file']
    output_file = args['output_file']
    test_val = args['test'] if args['test'] else input_file
    
    try:
        findings = parse_findings(
            parser_name=parser_name,
            input_file=input_file,
            test_label=test_val,
            output_file=output_file
        )
        
        if args['print']:
            for val in findings:
                print(val)
                
    except Exception as e:
        print(f"Error parsing {input_file} with {parser_name}: {e}")

def main():
    # Load mapping if exists
    mapping_path = os.path.join(os.path.dirname(__file__), "parser_mapping.json")
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            parser_mapping = json_lib.load(f)
    else:
        parser_mapping = {}

    # For choices, we can use keys of mapping or just list directory
    parsers = [p for p in parser_mapping.keys()] 
    if not parsers:
         # Fallback if mapping missing
         parsers = ["TrivyParser"] # Minimal fallback

    cli_parser = create_parser(parsers)
    args = cli_parser.parse_args()
    dargs = jsonargparse.namespace_to_dict(args)

    if args.subcommand == "convert":
        convert(dargs['convert'])
    elif args.subcommand == "server":
        try:
            import uvicorn
            from server import app 
            uvicorn.run(app, host='0.0.0.0', port=dargs['server']['port'])
        except ImportError:
            print("Error: Server dependencies not found. Install with: pip install norm-findings[server]")

if __name__ == "__main__":
    main()
