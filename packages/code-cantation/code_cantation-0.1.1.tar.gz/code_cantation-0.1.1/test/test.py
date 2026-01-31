#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import tempfile
from code_cantation.executor import Executor

# Use the module entry-point so you don't have to rely on PATH
CLI_CMD = [sys.executable, "-m", "code_cantation.cli"]


def test_script_as_library():
    print("=== Script as library ===")
    code = "a = 10; b = 5; print('sum is', a + b); result = a + b"
    exe = Executor()
    result = exe.execute(code=code)

    # assertions
    assert result.console_log.strip() == "sum is 15", "Expected console log 'sum is 15'"
    assert result.captured_output is None, "No return value for script mode"
    assert result.exec_error is None, "No execution error expected"
    print("PASS: script as library\n")


def test_function_no_params_as_library():
    print("=== Function without params as library ===")
    code = """
def greet():
    print('hello!')
    return 'hello'
"""
    exe = Executor()
    result = exe.execute(
        code=code,
        code_type="FUNCTION"
    )

    # assertions
    assert result.console_log.strip() == "hello!", "Expected console log 'hello!'"
    assert result.captured_output == 'hello', "Expected return 'hello'"
    assert result.exec_error is None, "No execution error expected"
    print("PASS: function no params as library\n")


def test_function_with_params_as_library():
    print("=== Function with params as library ===")
    code = """
def add(a, b):
    print('adding', a, b)
    return a + b
"""
    exe = Executor()
    result = exe.execute(
        code=code,
        code_type="FUNCTION",
        input_values=[7, 3]
    )

    # assertions
    assert result.console_log.strip() == "adding 7 3", "Expected console log 'adding 7 3'"
    assert result.captured_output == 10, "Expected return 10"
    assert result.exec_error is None, "No execution error expected"
    print("PASS: function with params as library\n")


def test_unsafe_module_as_library():
    print("=== Unsafe module import as library ===")
    code = "import requests"
    exe = Executor()
    result = exe.execute(code=code)

    # assertions
    assert result.safety_violation is not None, "Expected safety violation for import os"
    assert "Unsafe module import" in result.safety_violation, "Violation message should mention module import"
    print("PASS: unsafe module import as library\n")


def test_unsafe_function_as_library():
    print("=== Unsafe function call as library ===")
    code = "eval('1+1')"
    exe = Executor()
    result = exe.execute(code=code)

    # assertions
    assert result.safety_violation is not None, "Expected safety violation for eval"
    assert "Unsafe function" in result.safety_violation, "Violation message should mention function call"
    print("PASS: unsafe function call as library\n")


def test_timeout_as_library():
    print("=== Timeout as library ===")
    code = "while True: pass"
    exe = Executor()
    result = exe.execute(
        code=code,
        timeout_sec=1,
        cpu_time_limit_sec=1,
        memory_limit_mb=128
    )

    # assertions
    assert result.exec_error is not None, "Expected timeout error"
    assert "timed out" in result.exec_error.lower(), "Expected timeout message"
    print("PASS: timeout as library\n")


def test_allowed_root_as_library():
    print("=== Allowed root as library ===")
    base_dir = tempfile.mkdtemp()
    exe = Executor()

    ok_code = "open('ok.txt', 'w').write('ok')"
    ok_result = exe.execute(
        code=ok_code,
        allowed_root=base_dir,
        work_dir=base_dir
    )
    ok_path = os.path.join(base_dir, "ok.txt")
    assert ok_result.exec_error is None, "Expected no error writing inside allowed root"
    assert os.path.isfile(ok_path), "Expected file to be created inside allowed root"

    bad_code = "open('../nope.txt', 'w').write('nope')"
    bad_result = exe.execute(
        code=bad_code,
        allowed_root=base_dir,
        work_dir=base_dir
    )
    assert bad_result.exec_error is not None, "Expected error writing outside allowed root"
    assert "outside allowed root" in bad_result.exec_error.lower(), "Expected path restriction error"
    print("PASS: allowed root as library\n")


def test_allowed_root_defaults_to_root():
    print("=== Allowed root defaults to work dir ===")
    base_dir = tempfile.mkdtemp()
    exe = Executor()
    result = exe.execute(
        code="open('default.txt', 'w').write('ok')",
        allowed_root=base_dir
    )
    default_path = os.path.join(base_dir, "default.txt")
    assert result.exec_error is None, "Expected no error writing inside allowed root"
    assert os.path.isfile(default_path), "Expected file to be created in allowed root"
    print("PASS: allowed root defaults to work dir\n")


def test_work_dir_outside_root_rejected():
    print("=== Work dir outside root rejected ===")
    base_dir = tempfile.mkdtemp()
    outside_dir = os.path.dirname(base_dir)
    exe = Executor()
    result = exe.execute(
        code="print('hi')",
        allowed_root=base_dir,
        work_dir=outside_dir
    )
    assert result.exec_error is not None, "Expected error for work_dir outside allowed root"
    assert "work_dir must be within allowed_root" in result.exec_error, "Expected work_dir validation error"
    print("PASS: work dir outside root rejected\n")


def run_cli(args):
    return subprocess.run(
        CLI_CMD + args,
        capture_output=True,
        text=True
    )


def test_script_as_cli():
    print("=== Script via CLI ===")
    code = "print('CLI script'); x = 2 + 2; print('x =', x)"
    proc = run_cli(["--code", code])
    out = proc.stdout.strip().splitlines()

    # assertions
    assert "CLI script" in out[0], "Expected 'CLI script' in first line"
    assert "x = 4" in out[0], "Expected 'x = 4' in second line"
    print("PASS: script via CLI\n")


def test_function_no_params_as_cli():
    print("=== Function without params via CLI ===")
    code = "def greet():\n    print('hi there'); return 'hi there'"
    proc = run_cli([
        "--code", code,
        "--code-type", "FUNCTION"
    ])
    out = proc.stdout.strip()
    output_json = json.loads(out)

    # assertions
    assert "hi there" in output_json['console_log'], "Expected single-line output 'hi there'"
    print("PASS: function no params via CLI\n")


def test_function_with_params_as_cli():
    print("=== Function with params via CLI ===")
    code = "def mul(a, b):\n    print('mul', a, b); return a * b"
    input_args = json.dumps([4, 5])
    proc = run_cli([
        "--code", code,
        "--code-type", "FUNCTION",
        "--input", input_args
    ])
    out = proc.stdout.strip().splitlines()

    output_json = json.loads(out[0])
    # assertions
    assert "mul 4 5" in output_json['console_log'], "Expected 'mul 4 5' in console log"
    assert 20 == output_json['captured_output'], "Expected return value '20'"
    print("PASS: function with params via CLI\n")


def test_timeout_as_cli():
    print("=== Timeout via CLI ===")
    proc = run_cli([
        "--code", "while True: pass",
        "--timeout-sec", "1",
        "--cpu-time-limit-sec", "1",
        "--memory-limit-mb", "128"
    ])
    out = proc.stdout.strip()
    output_json = json.loads(out)
    assert output_json["exec_error"] is not None, "Expected timeout error via CLI"
    assert "timed out" in output_json["exec_error"].lower(), "Expected timeout message"
    print("PASS: timeout via CLI\n")


def test_allowed_root_as_cli():
    print("=== Allowed root via CLI ===")
    base_dir = tempfile.mkdtemp()
    proc = run_cli([
        "--code", "open('cli.txt','w').write('ok')",
        "--allowed-root", base_dir
    ])
    out = proc.stdout.strip()
    output_json = json.loads(out)
    cli_path = os.path.join(base_dir, "cli.txt")
    assert output_json["exec_error"] is None, "Expected no error writing inside allowed root"
    assert os.path.isfile(cli_path), "Expected file to be created inside allowed root"
    print("PASS: allowed root via CLI\n")


if __name__ == "__main__":
    test_script_as_library()
    test_function_no_params_as_library()
    test_function_with_params_as_library()
    test_unsafe_module_as_library()
    test_unsafe_function_as_library()
    test_timeout_as_library()
    test_allowed_root_as_library()
    test_allowed_root_defaults_to_root()
    test_work_dir_outside_root_rejected()

    test_script_as_cli()
    test_function_no_params_as_cli()
    test_function_with_params_as_cli()
    test_timeout_as_cli()
    test_allowed_root_as_cli()
