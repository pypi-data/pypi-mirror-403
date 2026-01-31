from typing import Dict, Callable
from .models import QueueTask, TaskResponse


class TaskProcessor:
    """任务处理器，用于处理不同类型的任务"""
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.processors: Dict[str, Callable] = {}
    
    def register_processor(self, endpoint: str, processor: Callable):
        """注册特定端点的处理器"""
        self.processors[endpoint] = processor
    
    async def process_task(self, task: QueueTask) -> TaskResponse:
        """处理单个任务"""
