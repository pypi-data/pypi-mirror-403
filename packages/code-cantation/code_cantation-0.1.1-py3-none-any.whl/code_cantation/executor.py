import os
import sys
import subprocess
import shlex
import multiprocessing as mp
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import queue as queue_module

from code_cantation.models import CodeExecutorOutput
from code_cantation.safety_checker import safety_check
from code_cantation.code_utils import CodeUtils


FS_AUDIT_EVENTS = {
    "open",
    "os.open",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "os.mkdir",
    "os.makedirs",
    "os.rename",
    "os.replace",
    "os.stat",
    "os.lstat",
    "os.listdir",
    "os.scandir",
    "os.chdir",
    "os.chmod",
    "os.chown",
    "os.truncate",
    "os.utime",
    "os.link",
    "os.symlink",
}


def _normalize_path(path):
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def _is_within_root(path, root):
    try:
        return os.path.commonpath([root, path]) == root
    except ValueError:
        return False


def _resolve_path(path, cwd):
    if isinstance(path, bytes):
        try:
            path = path.decode()
        except Exception:
            path = path.decode(errors="ignore")
    path = os.fspath(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return _normalize_path(path)


def _apply_resource_limits(cpu_time_limit_sec, memory_limit_mb):
    try:
        import resource
    except ImportError:
        return

    if cpu_time_limit_sec is not None and cpu_time_limit_sec > 0:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_sec, cpu_time_limit_sec))

    if memory_limit_mb is not None and memory_limit_mb > 0:
        bytes_limit = int(memory_limit_mb) * 1024 * 1024
        limit_type = getattr(resource, "RLIMIT_AS", None) or getattr(resource, "RLIMIT_DATA", None)
        if limit_type is not None:
            resource.setrlimit(limit_type, (bytes_limit, bytes_limit))


def _execute_in_subprocess(
    code,
    code_type,
    input_values,
    cpu_time_limit_sec,
    memory_limit_mb,
    allowed_root,
    work_dir,
    result_queue,
):
    f_out = StringIO()
    f_err = StringIO()
    captured_output = None
    exec_error = None
    console_log = ""
    try:
        allowed_root_norm = _normalize_path(allowed_root) if allowed_root else None
        work_dir_norm = _normalize_path(work_dir) if work_dir else None

        if allowed_root_norm:
            if work_dir_norm is None:
                work_dir_norm = allowed_root_norm
            if not _is_within_root(work_dir_norm, allowed_root_norm):
                raise PermissionError("work_dir must be within allowed_root")

            os.chdir(work_dir_norm)
            cwd_holder = [work_dir_norm]

            def audit_hook(event, args):
                if event not in FS_AUDIT_EVENTS:
                    return
                paths = []
                if event in {"os.rename", "os.replace", "os.link", "os.symlink"}:
                    if len(args) > 0:
                        paths.append(args[0])
                    if len(args) > 1:
                        paths.append(args[1])
                elif len(args) > 0:
                    paths.append(args[0])

                for raw_path in paths:
                    if not isinstance(raw_path, (str, bytes, os.PathLike)):
                        continue
                    resolved = _resolve_path(raw_path, cwd_holder[0])
                    if not _is_within_root(resolved, allowed_root_norm):
                        raise PermissionError(f"Path access outside allowed root: {resolved}")

                if event == "os.chdir" and paths:
                    cwd_holder[0] = _resolve_path(paths[0], cwd_holder[0])

            sys.addaudithook(audit_hook)

        _apply_resource_limits(cpu_time_limit_sec, memory_limit_mb)
        exec_globals = {"__builtins__": __builtins__}
        context = {}
        effective_code_type = code_type if code_type else CodeUtils.classify_code(code)
        with redirect_stdout(f_out), redirect_stderr(f_err):
            if effective_code_type == 'SCRIPT':
                exec(code, exec_globals)
            elif effective_code_type == 'FUNCTION':
                captured_output = Executor._execute_function(code, context, input_values)
            else:
                raise ValueError(f"Unknown code_type: {effective_code_type}")
        console_log = f_out.getvalue()
    except Exception as e:
        exec_error = str(e)
        console_log = f_out.getvalue()

    result_queue.put({
        "captured_output": captured_output,
        "console_log": console_log,
        "exec_error": exec_error,
    })


class Executor:

    def execute(self, code, run_safety=True, code_type=None, input_values=None,
                unsafe_modules=None, unsafe_functions=None, override_default_safety=False,
                timeout_sec=5, cpu_time_limit_sec=5, memory_limit_mb=256,
                allowed_root=None, work_dir=None):

        captured_output = None
        exec_error = None
        console_log = None
        if timeout_sec == 0:
            timeout_sec = None
        if cpu_time_limit_sec == 0:
            cpu_time_limit_sec = None
        if memory_limit_mb == 0:
            memory_limit_mb = None
        if allowed_root:
            allowed_root = _normalize_path(allowed_root)
            if work_dir:
                work_dir = _normalize_path(work_dir)
                if not _is_within_root(work_dir, allowed_root):
                    return CodeExecutorOutput(exec_error="work_dir must be within allowed_root")
            else:
                work_dir = allowed_root

        safety_result = self._is_safe_to_run(code, run_safety, unsafe_modules, unsafe_functions, override_default_safety)
        if safety_result["safe"]:
            code_type = code_type if code_type else CodeUtils.classify_code(code)
            try:
                ctx = mp.get_context("spawn")
                result_queue = ctx.Queue(maxsize=1)
                process = ctx.Process(
                    target=_execute_in_subprocess,
                    args=(
                        code,
                        code_type,
                        input_values,
                        cpu_time_limit_sec,
                        memory_limit_mb,
                        allowed_root,
                        work_dir,
                        result_queue,
                    ),
                )
                process.start()
                process.join(timeout_sec if timeout_sec else None)
                if process.is_alive():
                    process.terminate()
                    process.join()
                    exec_error = f"Execution timed out after {timeout_sec} seconds"
                    return CodeExecutorOutput(exec_error=exec_error)

                try:
                    result = result_queue.get_nowait()
                except queue_module.Empty:
                    if process.exitcode is not None and process.exitcode < 0:
                        exec_error = f"Execution terminated by signal {-process.exitcode}"
                    else:
                        exec_error = "Execution failed without returning output"
                    return CodeExecutorOutput(exec_error=exec_error)

                return CodeExecutorOutput(
                    captured_output=result.get("captured_output"),
                    console_log=result.get("console_log"),
                    exec_error=result.get("exec_error"),
                )
            except Exception as e:
                exec_error = str(e)
                return CodeExecutorOutput(exec_error=exec_error)
        else:
            return CodeExecutorOutput(safety_violation=safety_result['message'])




    @staticmethod
    def _is_safe_to_run(code, run_safety, unsafe_modules, unsafe_functions, override_default_safety):
        if run_safety:
            safety_result = safety_check(code, unsafe_modules, unsafe_functions, override_default_safety)
            return safety_result
        else:
            return {
                "safe": True,
                "message": "safety check disabled"
            }

    @staticmethod
    def _execute_shell_command(cmd):
        args = shlex.split(cmd)
        result = subprocess.run(args, capture_output=True, text=True)
        return result.stdout

    @staticmethod
    def _execute_function(code, context, input_values=None):
        exec(code, context)
        deconstructed_function = CodeUtils.deconstruct_function(code)

        if input_values:
            exec_statement = f'function_output = {deconstructed_function.function_name}(*{input_values})'
        else:
            exec_statement = f'function_output = {deconstructed_function.function_name}()'

        if exec_statement:
            exec(exec_statement, context)
        else:
            raise Exception('failed to create exec statement for function exec with args')

        captured_output = context['function_output']
        return captured_output
