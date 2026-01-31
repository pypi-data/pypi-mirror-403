"""
API documentation generator with Sphinx AutoAPI integration.
"""

import ast
import os
import inspect
from typing import List, Dict, Any, Optional
from .models import APIInfo, FunctionInfo


class APIGenerator:
    """
    Generates API documentation using Sphinx AutoAPI.
    
    Extracts docstrings, parameter types, and function signatures
    to create comprehensive API documentation.
    """
    
    def __init__(self):
        """Initialize the API generator."""
        pass
    
    def parse_module(self, module_path: str) -> APIInfo:
        """
        Parse a Python module and extract API information.
        
        Args:
            module_path: Path to the Python module file
            
        Returns:
            APIInfo: Extracted API information
        """
        with open(module_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        tree = ast.parse(source_code)
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        
        functions = []
        classes = []
        constants = {}
        imports = []
        
        # Extract module-level docstring
        module_docstring = self.extract_docstring(tree)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only include top-level functions (not nested or class methods)
                if isinstance(node.parent if hasattr(node, 'parent') else None, ast.Module) or not hasattr(node, 'parent'):
                    func_info = self.extract_function_info(node, module_path)
                    functions.append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'docstring': self.extract_docstring(node),
                    'methods': [],
                    'line_number': node.lineno
                }
                
                # Extract class methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = self.extract_function_info(item, module_path)
                        class_info['methods'].append(method_info)
                
                classes.append(class_info)
            
            elif isinstance(node, ast.Assign):
                # Extract module-level constants
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants[target.id] = ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                else:
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
        
        return APIInfo(
            module_name=module_name,
            functions=functions,
            classes=classes,
            constants=constants,
            imports=imports,
            docstring=module_docstring
        )
    
    def extract_function_info(self, func_node: ast.FunctionDef, module_path: str) -> FunctionInfo:
        """
        Extract information from a function AST node.
        
        Args:
            func_node: AST node representing a function
            module_path: Path to the module containing the function
            
        Returns:
            FunctionInfo: Extracted function information
        """
        docstring = self.extract_docstring(func_node)
        parameters = self.extract_type_annotations(func_node)
        
        # Extract return type annotation
        return_type = None
        if func_node.returns:
            if hasattr(ast, 'unparse'):
                return_type = ast.unparse(func_node.returns)
            else:
                return_type = str(func_node.returns)
        
        return FunctionInfo(
            name=func_node.name,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            module_path=module_path,
            line_number=func_node.lineno
        )
    
    def extract_docstring(self, node: ast.AST) -> Optional[str]:
        """
        Extract docstring from an AST node.
        
        Args:
            node: AST node (function, class, or module)
            
        Returns:
            Optional[str]: Extracted docstring or None
        """
        if not hasattr(node, 'body') or not node.body:
            return None
        
        first_stmt = node.body[0]
        if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant):
            if isinstance(first_stmt.value.value, str):
                return first_stmt.value.value
        elif isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Str):
            # For older Python versions
            return first_stmt.value.s
        
        return None
    
    def extract_type_annotations(self, func_node: ast.FunctionDef) -> Dict[str, str]:
        """
        Extract type annotations from a function.
        
        Args:
            func_node: Function AST node
            
        Returns:
            Dict[str, str]: Parameter names mapped to type annotations
        """
        parameters = {}
        
        for arg in func_node.args.args:
            param_name = arg.arg
            if arg.annotation:
                if hasattr(ast, 'unparse'):
                    param_type = ast.unparse(arg.annotation)
                else:
                    param_type = str(arg.annotation)
                parameters[param_name] = param_type
            else:
                parameters[param_name] = "Any"
        
        # Handle keyword-only arguments
        for arg in func_node.args.kwonlyargs:
            param_name = arg.arg
            if arg.annotation:
                if hasattr(ast, 'unparse'):
                    param_type = ast.unparse(arg.annotation)
                else:
                    param_type = str(arg.annotation)
                parameters[param_name] = param_type
            else:
                parameters[param_name] = "Any"
        
        return parameters
    
    def generate_sphinx_rst(self, api_info: APIInfo) -> str:
        """
        Generate Sphinx RST documentation from API information.
        
        Args:
            api_info: API information to document
            
        Returns:
            str: Generated RST content
        """
        rst_content = []
        
        # Module header
        module_title = f"{api_info.module_name} Module"
        rst_content.append(module_title)
        rst_content.append("=" * len(module_title))
        rst_content.append("")
        
        # Module docstring
        if api_info.docstring:
            rst_content.append(api_info.docstring)
            rst_content.append("")
        
        # Functions section
        if api_info.functions:
            rst_content.append("Functions")
            rst_content.append("-" * 9)
            rst_content.append("")
            
            for func in api_info.functions:
                rst_content.append(f".. autofunction:: {api_info.module_name}.{func.name}")
                rst_content.append("")
        
        # Classes section
        if api_info.classes:
            rst_content.append("Classes")
            rst_content.append("-" * 7)
            rst_content.append("")
            
            for cls in api_info.classes:
                rst_content.append(f".. autoclass:: {api_info.module_name}.{cls['name']}")
                rst_content.append("   :members:")
                rst_content.append("   :undoc-members:")
                rst_content.append("   :show-inheritance:")
                rst_content.append("")
        
        # Constants section
        if api_info.constants:
            rst_content.append("Constants")
            rst_content.append("-" * 9)
            rst_content.append("")
            
            for name, value in api_info.constants.items():
                rst_content.append(f".. autodata:: {api_info.module_name}.{name}")
                rst_content.append("")
        
        return "\n".join(rst_content)