from pydantic import BaseModel
from typing import List, Any, Optional


class DeconstructedFunction(BaseModel):
    function_name: str
    inputs: List[Any] = None
    outputs: List[Any] = None
    console_outputs: Optional[List[Any]] = None


class CodeExecutorOutput(BaseModel):
    captured_output: Optional[Any] = None
    console_log: Optional[str] = None
    exec_error : Optional[str] = None
    safety_violation: Optional[str] = None
