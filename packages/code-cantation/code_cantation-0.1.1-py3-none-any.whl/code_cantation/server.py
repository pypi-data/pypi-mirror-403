"""
FastAPI server that exposes one endpoint:
POST /execute { ...Executor kwargs... } ➜ CodeExecutorOutput JSON
"""
import asyncio
import json
from typing import Any, Dict, Optional, Literal, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from code_cantation.executor import Executor, CodeExecutorOutput


# ---------- Pydantic request model ----------
class ExecRequest(BaseModel):
    code: str
    run_safety: bool = True

    # Either value or None. Literal enforces the two allowed strings
    code_type: Optional[Literal["SCRIPT", "FUNCTION"]] = None

    input_values: Optional[list[Any]] = None
    unsafe_modules: Optional[List[str]] = None
    unsafe_functions: Optional[List[str]] = None
    override_default_safety: bool = False
    timeout_sec: Optional[int] = 5
    cpu_time_limit_sec: Optional[int] = 5
    memory_limit_mb: Optional[int] = 256
    allowed_root: Optional[str] = None
    work_dir: Optional[str] = None


# ---------- App + single-worker queue ----------
app = FastAPI(title="Code Cantation API")
request_queue: asyncio.Queue[ExecRequest] = asyncio.Queue(maxsize=100)
executor = Executor()


@app.on_event("startup")
async def start_worker():
    async def worker():
        while True:
            req: ExecRequest = await request_queue.get()
            try:
                result = executor.execute(
                    code=req.code,
                    run_safety=req.run_safety,
                    code_type=req.code_type,
                    input_values=req.input_values,
                    unsafe_modules=req.unsafe_modules,
                    unsafe_functions=req.unsafe_functions,
                    override_default_safety=req.override_default_safety,
                    timeout_sec=req.timeout_sec if req.timeout_sec != 0 else None,
                    cpu_time_limit_sec=req.cpu_time_limit_sec if req.cpu_time_limit_sec != 0 else None,
                    memory_limit_mb=req.memory_limit_mb if req.memory_limit_mb != 0 else None,
                    allowed_root=req.allowed_root,
                    work_dir=req.work_dir,
                )
                req._future.set_result(result)
            except Exception as e:  # should be rare because Executor handles its own errors
                req._future.set_exception(e)
            finally:
                request_queue.task_done()

    # detached worker task
    asyncio.create_task(worker())


@app.post("/execute")
async def execute(req: ExecRequest):
    """
    Queue the request; single background worker ensures only one snippet
    runs at a time (protects memory / CPU for heavy code).
    """
    if request_queue.full():
        raise HTTPException(status_code=429, detail="Server busy, try later")

    # attach a Future so we can get the result back
    loop = asyncio.get_running_loop()
    req._future: asyncio.Future[CodeExecutorOutput] = loop.create_future()

    await request_queue.put(req)
    result: CodeExecutorOutput = await req._future
    return json.loads(result.model_dump_json())
