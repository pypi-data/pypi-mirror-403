import ast


class SafetyVisitor(ast.NodeVisitor):
    def __init__(self):
        # We'll collect all violations here
        self.violations = []

        # Modules that should never be imported
        self.unsafe_modules = {
            "sys", "subprocess", "builtins", "requests", "socket", "http.client",
            "urllib.request", "importlib", "pickle", "ctypes"
        }

        # Functions (by name) that are considered unsafe
        self.unsafe_functions = {
            "exec", "eval", "compile", "input", "__import__",
            "getattr", "setattr", "delattr", "hasattr"
        }

        # Dangerous built-ins (there's some overlap with unsafe_functions)
        self.dangerous_builtins = {
            "globals", "locals", "vars", "dir", "eval", "exec", "compile"
        }

        # OS calls that are allowed
        self.safe_os_functions = {"path", "path.join", "join"}  # add more if needed

        # Track which variables are aliases to unsafe functions
        # For example, `x = eval` => any call to `x("...")` is also unsafe.
        self.alias_map = set()  # store variable names pointing to an unsafe function

    def report_violation(self, node, message):
        """Helper to record a violation with line/column info."""
        line = getattr(node, 'lineno', None)
        col = getattr(node, 'col_offset', None)
        self.violations.append(
            f"Line {line}, Col {col}: {message}"
        )

    def get_function_id(self, node):
        """
        Recursively get the 'base name' of a function call.
        For example:
            os.path.join -> 'os'
            os.system -> 'os'
            eval -> 'eval'
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self.get_function_id(node.value)
        else:
            return None

    def get_full_attr_path(self, node):
        """
        Get the full dotted path of an attribute, e.g. os.path.join => "os.path.join"
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            parent = self.get_full_attr_path(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return None

    def visit_Assign(self, node):
        """
        Catch simple reassignments: x = eval, y = exec, etc.
        If the value references an unsafe function or an alias to an unsafe function,
        mark the target as unsafe too.
        """
        # We only handle simple single-target assignments like x = ...
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            # Check if the value is a direct reference to an unsafe function or alias
            if isinstance(node.value, ast.Name):
                # e.g., x = eval
                if node.value.id in self.unsafe_functions or node.value.id in self.alias_map:
                    self.alias_map.add(target_name)
            elif isinstance(node.value, ast.Attribute):
                # e.g., x = builtins.eval
                full_path = self.get_full_attr_path(node.value)
                # If the base is something we forbid or if the result is an unsafe function
                if (full_path in self.unsafe_functions or
                        any(part in self.unsafe_functions for part in full_path.split("."))):
                    self.alias_map.add(target_name)

        self.generic_visit(node)

    def visit_Call(self, node):
        """
        Check all function calls:
          - direct calls to unsafe built-ins
          - calls via an alias
          - calls on 'os' outside a defined whitelist
        """
        # Check if the function is a simple name
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # 1) If function is in alias_map => unsafe
            if func_name in self.alias_map:
                self.report_violation(node, f"Call to aliased unsafe function: {func_name}")

            # 2) If function is in dangerous built-ins
            if func_name in self.dangerous_builtins:
                self.report_violation(node, f"Use of dangerous built-in function: {func_name}")

            # 3) If function is in unsafe_functions
            if func_name in self.unsafe_functions:
                self.report_violation(node, f"Unsafe function call: {func_name}")

        # Check if the function is an attribute (e.g., os.system)
        elif isinstance(node.func, ast.Attribute):
            full_path = self.get_full_attr_path(node.func)  # e.g. "os.system", "os.path.join"
            base = self.get_function_id(node.func)  # e.g. "os"
            attr = node.func.attr  # e.g. "system" or "join"

            # If the base is 'os', we only allow a small set of whitelisted calls
            if base == "os":
                # e.g. "os.path" or "os.path.join" is allowed, but "os.system" is not
                if full_path not in self.safe_os_functions:
                    self.report_violation(node, f"Unsafe function call: {full_path}")

            # Also check if the entire full_path is in unsafe_functions (in case something else is blacklisted)
            if full_path in self.unsafe_functions:
                self.report_violation(node, f"Unsafe function call: {full_path}")

        self.generic_visit(node)

    def visit_Import(self, node):
        """
        Check direct imports: import sys, import subprocess, etc.
        """
        for alias in node.names:
            module_root = alias.name.split(".")[0]
            if module_root in self.unsafe_modules:
                self.report_violation(node, f"Unsafe module import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Check 'from X import Y' type imports.
        """
        if node.module:
            module_root = node.module.split(".")[0]
            if module_root in self.unsafe_modules:
                self.report_violation(node, f"Unsafe module import: {node.module}")
        for alias in node.names:
            alias_root = alias.name.split(".")[0]
            if alias_root in self.unsafe_modules:
                self.report_violation(node, f"Unsafe module import: {alias.name}")
        self.generic_visit(node)


def safety_check(python_code: str, unsafe_modules, unsafe_functions, override_default_safety) -> dict:
    """
    Check if Python code is safe to execute, based on common unsafe patterns.
    This uses AST parsing plus custom logic to disallow or restrict certain modules and functions.

    Args:
        python_code: Python code to check

    Returns:
        Dictionary with:
          - "safe"   (bool)
          - "message" (str) either "The code is safe to execute." or a summary of violations
    """

    try:
        tree = ast.parse(python_code)
    except SyntaxError as e:
        return {
            "safe": False,
            "message": f"Syntax error: {str(e)}"
        }

    visitor = SafetyVisitor()

    if unsafe_modules:
        if override_default_safety:
            visitor.unsafe_modules = unsafe_modules
        else:
            visitor.unsafe_modules.update(unsafe_modules)

    if unsafe_functions:
        if override_default_safety:
            visitor.unsafe_functions = unsafe_functions
        else:
            visitor.unsafe_functions.update(unsafe_functions)

    visitor.visit(tree)

    if visitor.violations:
        # If we have any violations, return unsafe
        return {
            "safe": False,
            "message": "Violations found:\n  " + "\n  ".join(visitor.violations)
        }
    else:
        # No violations found
        return {
            "safe": True,
            "message": "The code is safe to execute."
        }
