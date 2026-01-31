from __future__ import annotations
import asyncio
import base64
import os
import time
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, Executor
import threading

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, field_validator

from .registry import get_handler
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # optional in prod, present in dev
from .types import TaskAssignment as SDKTaskAssignment, Completion as SDKCompletion, InputDescriptor as SDKInput


class InputDescriptor(BaseModel):
    name: str
    media_type: str
    ref: str = ""
    inline_json: str = ""
    inline_bytes: str = ""

    @field_validator("inline_bytes")
    def validate_base64(cls, v: str) -> str:
        if v:
            try:
                base64.b64decode(v)
            except Exception as _:
                raise ValueError("inline_bytes must be valid base64")
        return v


class TaskAssignment(BaseModel):
    activity_id: str
    workflow_instance_id: str
    run_id: str
    task_kind: str
    task_version: str
    inputs: list[InputDescriptor]
    upload_prefix: str
    soft_deadline_unix: int = 0
    heartbeat_interval_s: int = 30


class TaskStatus(BaseModel):
    status: str = "pending"
    progress: int = Field(default=0, ge=0, le=100)
    result_refs: Optional[list[str]] = None
    result_map: Optional[dict[str, str]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskResponse(BaseModel):
    message: str
    task_id: str


def _to_sdk_assignment(assignment: TaskAssignment) -> SDKTaskAssignment:
    sdk_inputs = [
        SDKInput(
            name=i.name,
            media_type=i.media_type,
            ref=i.ref or None,
            inline_json=i.inline_json or None,
            inline_bytes=base64.b64decode(i.inline_bytes) if i.inline_bytes else None,
        )
        for i in assignment.inputs
    ]
    return SDKTaskAssignment(
        activity_id=assignment.activity_id,
        workflow_instance_id=assignment.workflow_instance_id,
        run_id=assignment.run_id,
        task_kind=assignment.task_kind,
        task_version=assignment.task_version,
        inputs=sdk_inputs,
        upload_prefix=assignment.upload_prefix,
        soft_deadline_unix=assignment.soft_deadline_unix,
        heartbeat_interval_s=assignment.heartbeat_interval_s,
    )


_EXECUTOR: Optional[Executor] = None
_TASKS_LOCK = threading.RLock()
_CFG: Optional[dict] = None


def _load_cfg() -> dict:
    global _CFG
    if _CFG is not None:
        return _CFG or {}
    paths = [
        os.environ.get("WEP_CONFIG"),
        "wep.local.yaml",
        os.path.join(os.getcwd(), "wep.local.yaml"),
        os.path.join(os.getcwd(), "python-wep-ex", "wep.local.yaml"),
    ]
    for p in paths:
        if p and os.path.isfile(p) and yaml is not None:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _CFG = yaml.safe_load(f) or {}
                return _CFG or {}
            except Exception:
                break
    _CFG = {}
    return {}


def _get_executor() -> Executor:
    global _EXECUTOR
    if _EXECUTOR is None:
        max_workers = int(os.environ.get("WEP_MAX_WORKERS", str(max(4, (os.cpu_count() or 4)))))
        _EXECUTOR = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="wep")
    return _EXECUTOR


def create_app() -> FastAPI:
    tasks: Dict[str, TaskStatus] = {}
    running_tasks: Dict[str, asyncio.Task] = {}

    app = FastAPI(title="Poseidon WEP REST", version="1.0.0")

    async def update_progress(task_id: str):
        try:
            for i in range(10):
                await asyncio.sleep(1)
                with _TASKS_LOCK:
                    if tasks.get(task_id) and tasks[task_id].status == "running":
                        tasks[task_id].progress = (i + 1) * 10
        except asyncio.CancelledError:
            pass

    async def process_task(task_id: str, assignment: TaskAssignment):
        try:
            with _TASKS_LOCK:
                tasks[task_id].status = "running"
                tasks[task_id].started_at = time.time()

            # Print raw URL for audio.handle_speech_quality tasks
            if assignment.task_kind == "audio.handle_speech_quality":
                for i in assignment.inputs:
                    if i.name == "raw_audio_file_object_key" and i.ref:
                        print(f"WEP: audio.handle_speech_quality raw URL: {i.ref}")

            # Pass refs through unchanged; WCP ensures refs are local file paths
            normalized_inputs = []
            for i in assignment.inputs:
                ref = i.ref
                normalized_inputs.append(InputDescriptor(name=i.name, media_type=i.media_type, ref=ref, inline_json=i.inline_json, inline_bytes=i.inline_bytes))
            assignment.inputs = normalized_inputs
            sdk_assignment = _to_sdk_assignment(assignment)
            handler = get_handler(assignment.task_kind, assignment.task_version)
            if not handler:
                raise ValueError(f"No handler for {assignment.task_kind}:{assignment.task_version}")

            prog = asyncio.create_task(update_progress(task_id))
            try:
                loop = asyncio.get_running_loop()
                executor = _get_executor()
                result: SDKCompletion = await loop.run_in_executor(executor, handler, sdk_assignment)
                with _TASKS_LOCK:
                    tasks[task_id].status = "completed"
                    tasks[task_id].progress = 100
                    # Multiple results passthrough (WCP uploads later)
                    if getattr(result, "result_refs", None):
                        tasks[task_id].result_refs = list(result.result_refs or [])
                    if getattr(result, "result_map", None):
                        tasks[task_id].result_map = dict(result.result_map or {})
                    tasks[task_id].completed_at = time.time()
            finally:
                prog.cancel()
        except Exception as e:
            with _TASKS_LOCK:
                tasks[task_id].status = "failed"
                tasks[task_id].error = str(e)
                tasks[task_id].completed_at = time.time()
        finally:
            running_tasks.pop(task_id, None)

    @app.post("/tasks/{task_id}/assign", status_code=202, response_model=TaskResponse)
    async def assign_task(task_id: str, assignment: TaskAssignment, background_tasks: BackgroundTasks):
        with _TASKS_LOCK:
            if task_id in tasks:
                raise HTTPException(status_code=409, detail=f"Task {task_id} already exists")
        if task_id != assignment.activity_id:
            raise HTTPException(status_code=400, detail=f"Task ID {task_id} does not match activity_id {assignment.activity_id}")
        with _TASKS_LOCK:
            tasks[task_id] = TaskStatus(status="pending")
        t = asyncio.create_task(process_task(task_id, assignment))
        running_tasks[task_id] = t
        return TaskResponse(message="Task accepted for processing", task_id=task_id)

    @app.get("/tasks/{task_id}/status", response_model=TaskStatus)
    async def get_task_status(task_id: str):
        with _TASKS_LOCK:
            if task_id not in tasks:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            return tasks[task_id]

    @app.get("/health")
    async def health_check():
        with _TASKS_LOCK:
            total_tasks = len(tasks)
            running = sum(1 for t in tasks.values() if t.status == "running")
            completed = sum(1 for t in tasks.values() if t.status == "completed")
            failed = sum(1 for t in tasks.values() if t.status == "failed")
        return {"status": "healthy", "tasks": {"total": total_tasks, "running": running, "completed": completed, "failed": failed}}

    return app


def run_wep_server():
    cfg = _load_cfg()
    server_cfg = cfg.get("server", {}) if isinstance(cfg, dict) else {}
    host = (server_cfg.get("host") if isinstance(server_cfg, dict) else None) or os.environ.get("WEP_HOST", "127.0.0.1")
    port_val = (server_cfg.get("port") if isinstance(server_cfg, dict) else None)
    try:
        port = int(os.environ.get("WEP_PORT") or (str(port_val) if port_val is not None else "8080"))
    except Exception:
        port = 8080
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")




