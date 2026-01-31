from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class UpdateTaskControllerInput:
    task: Dict[str, Any]
    webhook_url: str
    completed: bool
    channel_id: str = ""


@dataclass
class UpdateTaskControllerOutput:
    message: str
    status: int
    metadata: Dict[str, str] = field(default_factory=dict)
