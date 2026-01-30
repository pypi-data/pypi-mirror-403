import ast
import astunparse
import os

class ParserConverter(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.needed_stubs = set()

    def visit_ImportFrom(self, node):
        if node.module:
            if node.module == 'datetime':
                # Remove 'UTC' from 'from datetime import ...' if present
                new_names = [alias for alias in node.names if alias.name != 'UTC']
                if not new_names:
                    return None
                node.names = new_names
                
            if node.module.startswith('dojo.models') or node.module == 'dojo.models':
                node.module = 'norm_findings.stubs.models'
                for alias in node.names:
                    self.needed_stubs.add(alias.name)
                return node
            
            if node.module.startswith('dojo.utils') or node.module == 'dojo.utils' or node.module == 'dojo.validators' or node.module.startswith('dojo.notifications'):
                node.module = 'norm_findings.stubs.utils'
                return node

            if node.module == 'dojo.tools.utils':
                node.module = 'norm_findings.stubs.utils'
                return node

            if node.module.startswith('dojo.tools.'):
                # Map 'from dojo.tools.foo import bar' to 'from dojocli.parsers.foo import bar'
                node.module = node.module.replace('dojo.tools.', 'norm_findings.parsers.')
                return node

            if node.module.startswith('django.') or node.module == 'django':
                # Map 'from django.foo import bar' to 'from dojocli.stubs.django.foo import bar'
                node.module = node.module.replace('django', 'norm_findings.stubs.django')
                return node

            if node.module.startswith('dojo'):
                # Remove other dojo imports
                return None
            
        return node

    def visit_Import(self, node):
        new_names = []
        for alias in node.names:
            if alias.name.startswith('django'):
                alias.name = alias.name.replace('django', 'norm_findings.stubs.django')
                new_names.append(alias)
            elif not alias.name.startswith('dojo'):
                new_names.append(alias)
        if not new_names:
            return None
        node.names = new_names
        return node

    def visit_Name(self, node):
        if node.id == 'UTC':
            # Replace 'UTC' name with 'datetime.timezone.utc'
            return ast.Attribute(
                value=ast.Attribute(value=ast.Name(id='datetime', ctx=ast.Load()), attr='timezone', ctx=ast.Load()),
                attr='utc',
                ctx=ast.Load()
            )
        return node

    def visit_BinOp(self, node):
        # Translate 'TypeA | TypeB' (3.10+) to 'Union[TypeA, TypeB]'
        if isinstance(node.op, ast.BitOr):
            return ast.Subscript(
                value=ast.Attribute(value=ast.Name(id='typing', ctx=ast.Load()), attr='Union', ctx=ast.Load()),
                slice=ast.Index(value=ast.Tuple(elts=[node.left, node.right], ctx=ast.Load())),
                ctx=ast.Load()
            )
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        # Translate datetime.UTC (3.11+) to datetime.timezone.utc (compatible)
        if isinstance(node.value, ast.Name) and node.value.id == 'datetime' and node.attr == 'UTC':
            # Replace 'datetime.UTC' with 'datetime.timezone.utc'
            return ast.Attribute(
                value=ast.Attribute(value=ast.Name(id='datetime', ctx=ast.Load()), attr='timezone', ctx=ast.Load()),
                attr='utc',
                ctx=ast.Load()
            )
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        # Track direct calls to Finding() or Endpoint()
        if isinstance(node.func, ast.Name):
            if node.func.id in ['Finding', 'Endpoint']:
                self.needed_stubs.add(node.func.id)
            
            # Handle isinstance(x, A | B) -> isinstance(x, (A, B))
            if node.func.id == 'isinstance' and len(node.args) == 2:
                node.args[1] = self.ensure_tuple_for_isinstance(node.args[1])

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        if node.name == 'get_findings':
            # Standardize to (self, scan_file, test, ...)
            if len(node.args.args) >= 3:
                old_file_arg = node.args.args[1].arg
                old_test_arg = node.args.args[2].arg
                
                node.args.args[1].arg = 'scan_file'
                node.args.args[2].arg = 'test'
                
                # We need to rename usages in the body, but carefully.
                # A simple transformer walk works since this is a method scope.
                class VariableRenamer(ast.NodeTransformer):
                    def __init__(self, mapping):
                        self.mapping = mapping
                    def visit_Name(self, n):
                        if n.id in self.mapping:
                            n.id = self.mapping[n.id]
                        return n

                renamer = VariableRenamer({old_file_arg: 'scan_file', old_test_arg: 'test'})
                for i in range(len(node.body)):
                    node.body[i] = renamer.visit(node.body[i])
                    
        self.generic_visit(node)
        return node

    def ensure_tuple_for_isinstance(self, node):
        # If it's A | B, return (A, B)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            left = self.ensure_tuple_for_isinstance(node.left)
            right = self.ensure_tuple_for_isinstance(node.right)
            elts = []
            if isinstance(left, ast.Tuple): elts.extend(left.elts)
            else: elts.append(left)
            if isinstance(right, ast.Tuple): elts.extend(right.elts)
            else: elts.append(right)
            return ast.Tuple(elts=elts, ctx=ast.Load())
        return node

def convert_parser(input_path, output_path):
    with open(input_path, 'r') as f:
        source = f.read()
    
    tree = ast.parse(source)
    converter = ParserConverter()
    new_tree = converter.visit(tree)
    
    # Add a header and ensure typing is imported if needed
    header = "# Converted from DefectDojo parser\n"
    header += "import typing\n"
    header += "import datetime\n" # Ensure datetime is available for our UTC replacement
    header += "# Required stubs: " + ", ".join(converter.needed_stubs) + "\n"
    
    new_source = astunparse.unparse(new_tree)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(header)
        f.write(new_source)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        convert_parser(sys.argv[1], sys.argv[2])
