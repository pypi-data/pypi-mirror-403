import ast
from dill.source import getsource
from typing import Literal
from code_cantation.models import DeconstructedFunction


class CodeUtils:

    @staticmethod
    def parse_function( func):
        if isinstance(func, str):
            func_str = func
        else:
            func_str = getsource(func)
        parsed_code = ast.parse(func_str)

        return parsed_code

    @staticmethod
    def classify_code(code: str) -> Literal['FUNCTION', 'SCRIPT']:
        """
        Return 'function' if the code consists only of function definitions
        (and perhaps a module docstring), otherwise 'script'.
        """
        tree = ast.parse(code)
        # Filter out a leading docstring Expr(Str)
        nodes = [
            node for node in tree.body
            if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Str))
        ]

        # Count which nodes are function defs vs anything else
        func_defs = sum(isinstance(node, ast.FunctionDef) for node in nodes)
        others = len(nodes) - func_defs

        if func_defs > 0 and others == 0:
            return 'FUNCTION'
        return 'SCRIPT'

    @classmethod
    def deconstruct_function(cls, function):

        inputs = []
        console_outputs = []
        outputs = []
        function_name = None

        function_tree = cls.parse_function(function)

        for node in ast.walk(function_tree):
            # Check for function definitions to extract their arguments
            if isinstance(node, ast.FunctionDef):
                # note: if deconstruct fails because of lack of function then it might be better to fall back to
                # direct execution mode
                function_name = node.name

                for arg in node.args.args:
                    input_detail = {"arg": arg.arg, "type": None}
                    if arg.annotation:
                        input_detail["type"] = ast.unparse(arg.annotation)
                    inputs.append(input_detail)

            # Check for return statements
            if isinstance(node, ast.Return):
                if node.value:
                    return_expr = ast.unparse(node.value)
                    outputs.append({"type": "return", "expression": return_expr})

            # Check for print statements/function calls
            if isinstance(node, ast.Expr):
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
                    print_content = ", ".join(ast.unparse(arg) for arg in node.value.args)
                    console_outputs.append({"type": "print", "content": print_content})

        deconstructed_function = DeconstructedFunction(function_name=function_name, inputs=inputs, outputs=outputs, console_outputs=console_outputs)

        return deconstructed_function