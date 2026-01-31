#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
import json
import importlib
from code_cantation.models import CodeExecutorOutput
from code_cantation.executor import Executor


def _install_packages(args):
    if len(args.install) == 1 and os.path.isfile(args.install[0]):
        # treat single argument as a requirements file
        req_file = args.install[0]
        print(f"Installing from requirements file: {req_file}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file],
            check=True
        )
    else:
        # treat list as package names
        print(f"Installing packages: {' '.join(args.install)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + args.install,
            check=True
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run CodeCantation’s Executor from the command line"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--server", action="store_true",
                      help="Start FastAPI server instead of running code")
    mode.add_argument("-c", "--code",
                      help="Inline code string to execute")
    mode.add_argument("-f", "--file",
                      help="Path to a .py file containing the code to execute")

    # --- server-only options ---
    parser.add_argument("--host", default="0.0.0.0",
                        help="Server host (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Server port (default 8000)")

    parser.add_argument(
        "--install",
        nargs="+",
        metavar="PKG_OR_REQ",
        help=(
            "Optional: list of packages to install (e.g. requests numpy) "
            "or a single requirements file (e.g. requirements.txt) "
            "before running the code."
        )
    )

    parser.add_argument(
        "--no-safety",
        action="store_true",
        help="Disable safety checks (equivalent to run_safety=False)"
    )
    parser.add_argument(
        "--code-type",
        choices=["SCRIPT", "FUNCTION"],
        help="Force code type (otherwise auto-classified)"
    )
    parser.add_argument(
        "-i", "--input",
        help="JSON array of input values for function calls, e.g. '[1,2,3]'"
    )
    parser.add_argument(
        "--unsafe-modules",
        nargs="*",
        default=[],
        help="List of module names to treat as safe"
    )
    parser.add_argument(
        "--unsafe-functions",
        nargs="*",
        default=[],
        help="List of function names to treat as safe"
    )
    parser.add_argument(
        "--override-default-safety",
        action="store_true",
        help="Override any built-in safety defaults"
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=5,
        help="Wall-clock timeout for code execution (0 disables)"
    )
    parser.add_argument(
        "--cpu-time-limit-sec",
        type=int,
        default=5,
        help="CPU time limit for the execution process (0 disables)"
    )
    parser.add_argument(
        "--memory-limit-mb",
        type=int,
        default=256,
        help="Memory limit for the execution process in MB (0 disables)"
    )
    parser.add_argument(
        "--allowed-root",
        help="Restrict file access to this directory (read/write). Defaults work dir to this path."
    )
    parser.add_argument(
        "--work-dir",
        help="Working directory for code execution (must be within allowed root)."
    )

    args = parser.parse_args()

    # ---------- SERVER MODE ----------
    if args.server:
        # optional bulk install (same logic you already had)
        if args.install:
            _install_packages(args)

        # lazy import to avoid FastAPI dep unless needed
        try:
            server_mod = importlib.import_module("code_cantation.server")
            import uvicorn
        except ModuleNotFoundError as exc:
            missing = exc.name or "fastapi/uvicorn"
            print(
                f"Missing optional dependency '{missing}'. "
                "Install server extras with: pip install code-cantation[server]",
                file=sys.stderr
            )
            raise
        print(f"Starting server on {args.host}:{args.port} …")
        uvicorn.run(server_mod.app, host=args.host, port=args.port)
        return

    # If requested, install packages or requirements file first
    if args.install:
        _install_packages(args)

    # Load the code
    if args.file:
        with open(args.file, "r") as fp:
            code = fp.read()
    else:
        code = args.code

    # Parse input values for function, if any
    input_values = None
    if args.input:
        try:
            input_values = json.loads(args.input)
        except json.JSONDecodeError as e:
            parser.error(f"Invalid JSON for --input: {e}")

    # Execute
    timeout_sec = None if args.timeout_sec == 0 else args.timeout_sec
    cpu_time_limit_sec = None if args.cpu_time_limit_sec == 0 else args.cpu_time_limit_sec
    memory_limit_mb = None if args.memory_limit_mb == 0 else args.memory_limit_mb
    executor = Executor()
    result: CodeExecutorOutput = executor.execute(
        code=code,
        run_safety=not args.no_safety,
        code_type=args.code_type,
        input_values=input_values,
        unsafe_modules=args.unsafe_modules,
        unsafe_functions=args.unsafe_functions,
        override_default_safety=args.override_default_safety,
        timeout_sec=timeout_sec,
        cpu_time_limit_sec=cpu_time_limit_sec,
        memory_limit_mb=memory_limit_mb,
        allowed_root=args.allowed_root,
        work_dir=args.work_dir,
    )

    print(result.model_dump_json())


if __name__ == "__main__":
    main()
