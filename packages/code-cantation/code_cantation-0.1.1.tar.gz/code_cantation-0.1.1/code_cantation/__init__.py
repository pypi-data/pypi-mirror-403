# code_cantation/__init__.py
"""
code_cantation – safe code execution utilities
"""

# Re-export for convenient top-level import
from code_cantation.executor import Executor, CodeExecutorOutput

__all__ = ["Executor", "CodeExecutorOutput"]
