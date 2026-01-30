import os
import subprocess
import shutil
import json
import ast
import astunparse
from norm_findings.converter import convert_parser

DEFECT_DOJO_URL = "https://github.com/DefectDojo/django-DefectDojo.git"
TEMP_DIR = "tmp_defectdojo"
PARSERS_DIR = "norm_findings/parsers"
TEST_DATA_DIR = "test_data"

def fetch_defectdojo():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    print(f"Cloning DefectDojo from {DEFECT_DOJO_URL}...")
    subprocess.run(["git", "clone", "--depth", "1", DEFECT_DOJO_URL, TEMP_DIR], check=True)

def get_available_stubs():
    import norm_findings.stubs.models as models
    import inspect
    return {name for name, obj in inspect.getmembers(models) if inspect.isclass(obj)}

def update_parsers():
    tools_dir = os.path.join(TEMP_DIR, "dojo/tools")
    
    if not os.path.exists(tools_dir):
        fetch_defectdojo()
    
    parser_mapping = {}
    available_stubs = get_available_stubs()
    
    success = []
    failed = []
    
    for tool_name in os.listdir(tools_dir):
        tool_path = os.path.join(tools_dir, tool_name)
        if not os.path.isdir(tool_path):
            continue
            
        target_dir = os.path.join(PARSERS_DIR, tool_name)
        os.makedirs(target_dir, exist_ok=True)
        
        has_parser = False
        tool_missing_stubs = set()
        
        for root, dirs, files in os.walk(tool_path):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), tool_path)
                    parser_file = os.path.join(root, file)
                    target_file = os.path.join(target_dir, rel_path)
                    
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    
                    print(f"Converting {tool_name}/{rel_path}...")
                    try:
                        from norm_findings.converter import convert_parser, ParserConverter
                        # We still parse it here to get needed_stubs, but convert_parser will do the work
                        with open(parser_file, 'r') as f:
                            source = f.read()
                        tree = ast.parse(source)
                        converter = ParserConverter()
                        converter.visit(tree) # Just to collect stubs
                        
                        tool_missing_stubs.update(converter.needed_stubs - available_stubs)
                        
                        convert_parser(parser_file, target_file)

                        if rel_path == "parser.py":
                            has_parser = True
                            parser_mapping[tool_name] = target_file
                            
                    except Exception as e:
                        print(f"Failed to convert {tool_name}/{rel_path}: {e}")
                        failed.append({"tool": f"{tool_name}/{rel_path}", "reason": str(e)})

        if has_parser:
            if tool_missing_stubs:
                failed.append({"tool": tool_name, "reason": f"Missing stubs: {', '.join(tool_missing_stubs)}"})
            else:
                success.append(tool_name)

    # Save mapping
    with open("norm_findings/parser_mapping.json", 'w') as f:
        json.dump(parser_mapping, f, indent=4)
    
    # Generate summary
    with open("update_summary.md", 'w') as f:
        f.write("# DefectDojo Update Summary\n\n")
        f.write(f"Successfully converted {len(success)} parsers.\n")
        f.write(f"Found {len(failed)} parsers requiring manual intervention.\n\n")
        
        if failed:
            f.write("## Manual Action Required\n")
            f.write("The following parsers require additional stubs or have errors:\n\n")
            for item in failed:
                f.write(f"- **{item['tool']}**: {item['reason']}\n")
        
        if success:
            f.write("\n## Successfully Updated\n")
            f.write("- " + ", ".join(success[:10]) + (f" and {len(success)-10} more..." if len(success) > 10 else ""))

def update_tests():
    if not os.path.exists(TEMP_DIR):
        fetch_defectdojo()
    
    scans_src = os.path.join(TEMP_DIR, "unittests/scans")
    if os.path.exists(scans_src):
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        shutil.copytree(scans_src, TEST_DATA_DIR)
        print(f"Sample data copied to {TEST_DATA_DIR}")
    else:
        print(f"Warning: Sample data not found in {scans_src}")

if __name__ == "__main__":
    update_parsers()
    update_tests()
