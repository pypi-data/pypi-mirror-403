from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class InputDescriptor:
    name: str
    media_type: str
    ref: Optional[str] = None
    inline_json: Optional[str] = None
    inline_bytes: Optional[bytes] = None

@dataclass
class TaskAssignment:
    activity_id: str
    workflow_instance_id: str
    run_id: str
    task_kind: str
    task_version: str
    inputs: List[InputDescriptor]
    upload_prefix: str
    soft_deadline_unix: int
    heartbeat_interval_s: int

@dataclass
class Progress:
    activity_id: str
    run_id: str
    percent: int
    message: str = ""
    checkpoint_ref: Optional[str] = None

@dataclass
class Completion:
    activity_id: str
    run_id: str
    status: str
    result_refs: Optional[List[str]] = None
    result_map: Optional[Dict[str, str]] = None
    result_inline: Optional[bytes] = None
    error: Optional[str] = None

# --- SDK utilities for handlers ---
def get_input_ref(assign: TaskAssignment, name: str) -> str:
    """Return the ref for an input by name, or empty string."""
    try:
        for i in getattr(assign, "inputs", []) or []:
            if getattr(i, "name", "") == name and getattr(i, "ref", ""):
                return getattr(i, "ref")
    except Exception:
        pass
    return ""


def get_input_json(assign: TaskAssignment, name: str) -> Optional[str]:
    """Return inline_json for an input by name, or None."""
    try:
        for i in getattr(assign, "inputs", []) or []:
            if getattr(i, "name", "") == name and getattr(i, "inline_json", ""):
                return getattr(i, "inline_json")
    except Exception:
        pass
    return None


__all__ = [
    "InputDescriptor",
    "TaskAssignment",
    "Progress",
    "Completion",
    "get_input_ref",
    "get_input_json",
]
