from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class EventBusConfig(BaseModel):
    url: str
    topic: str


class TaskData(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = None
    stream: Optional[bool] = None


class QueueTask(BaseModel):
    ak: str
    endpoint: str
    queue: str
    level: int
    data: dict
    status: Optional[str] = None
    task_id: str
    batch_id: Optional[str] = None
    trace_id: Optional[str] = None
    instance_id: Optional[str] = None
    start_time: int
    running_time: int
    expire_time: int
    completed_time: int
    callback_url: Optional[str] = None
    response_mode: Literal["batch", "blocking", "streaming", "callback"]


class TaskRequest(BaseModel):
    queues: List[str]
    size: int = 10
    strategy: Literal["fifo", "round_robin", "active_passive", "sequential"] = "fifo"


class TaskResponse(BaseModel):
    status_code: int
    request_id: str
    body: Dict[str, Any]


class TaskProgressEvent(BaseModel):
    name: str = "task-progress-event"
    from_: str = Field(default="", alias="from")
    payload: Dict[str, Any]
    context: str = ""


class TaskCompletionEvent(BaseModel):
    name: str = "task-completion-event"
    from_: str = Field(default="", alias="from")
    payload: Dict[str, Any]
    context: str = ""


class ProgressEventPayload(BaseModel):
    taskId: str
    eventId: str
    eventName: str
    eventData: Dict[str, Any]


class CompletionEventPayload(BaseModel):
    taskId: str
    result: Dict[str, Any]