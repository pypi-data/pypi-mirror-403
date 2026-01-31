from typing import List, Optional
import os
from pydantic import BaseModel, Field


class WorkerConfig(BaseModel):
    """Worker配置"""
    
    # Bella Queue API配置
    host: str = Field(..., description="Bella Queue API主机地址")
    api_key: str = Field(..., description="API密钥")
    
    # 队列配置
    queues: List[str] = Field(default_factory=list, description="要处理的队列列表，格式：队列名:优先级")
    poll_interval: int = Field(default=5, description="轮询间隔（秒）")
    batch_size: int = Field(default=10, description="每次拉取任务数量")
    strategy: str = Field(default="fifo", description="队列拉取策略")
    
    # 处理配置
    task_timeout: int = Field(default=300, description="任务处理超时时间（秒）")
    max_concurrent_tasks: int = Field(default=10, description="最大并发任务数")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    
    @classmethod
    def from_env(cls) -> "WorkerConfig":
        """从环境变量创建配置"""
        return cls(
            host=os.getenv("BELLA_HOST", ""),
            api_key=os.getenv("BELLA_API_KEY", ""),
            queues=os.getenv("BELLA_QUEUES", "").split(",") if os.getenv("BELLA_QUEUES") else [],
            poll_interval=int(os.getenv("BELLA_POLL_INTERVAL", "5")),
            batch_size=int(os.getenv("BELLA_BATCH_SIZE", "10")),
            strategy=os.getenv("BELLA_STRATEGY", "fifo"),
            task_timeout=int(os.getenv("BELLA_TASK_TIMEOUT", "300")),
            max_concurrent_tasks=int(os.getenv("BELLA_MAX_CONCURRENT_TASKS", "10")),
            log_level=os.getenv("BELLA_LOG_LEVEL", "INFO")
        )