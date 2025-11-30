from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Column, Text, BigInteger, DateTime, Identity, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class TaskType(str, Enum):
    CRON = "cron"  # Cron expression
    INTERVAL = "interval"  # Interval in seconds
    DATE = "date"  # One-time execution at specific date


class ScheduledTask(SQLModel, table=True):
    """Scheduled task definition"""
    __tablename__ = "scheduled_task"
    
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    name: str = Field(max_length=255)
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    
    # Task type: cron, interval, date
    task_type: str = Field(max_length=50, default="cron")
    
    # Cron expression (for cron type)
    cron_expression: Optional[str] = Field(max_length=255, nullable=True)
    
    # Interval in seconds (for interval type)
    interval_seconds: Optional[int] = Field(sa_column=Column(Integer, nullable=True))
    
    # Scheduled date (for date type)
    scheduled_date: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    
    # Task action configuration (JSON)
    action_type: str = Field(max_length=50)  # http_request, sql_query, python_script
    action_config: Optional[dict] = Field(sa_column=Column(JSONB), default={})
    
    # Status
    enabled: Optional[bool] = Field(sa_column=Column(Boolean, default=True))
    status: str = Field(max_length=50, default="pending")
    
    # Retry configuration
    max_retries: Optional[int] = Field(default=3)
    retry_delay: Optional[int] = Field(default=60)  # seconds
    
    # Timestamps
    create_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    update_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    last_run_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    next_run_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    
    # Creator
    created_by: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))


class TaskLog(SQLModel, table=True):
    """Task execution log"""
    __tablename__ = "task_log"
    
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    task_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    
    # Execution details
    start_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    end_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    duration_ms: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    
    # Status and result
    status: str = Field(max_length=50, default="running")
    result: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    error_message: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    
    # Retry info
    retry_count: Optional[int] = Field(default=0)


class ScheduledTaskInfo(BaseModel):
    """Scheduled task info for API"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    task_type: str = "cron"
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    action_type: str
    action_config: Optional[dict] = {}
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60
    status: Optional[str] = "pending"
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class TaskLogInfo(BaseModel):
    """Task log info for API"""
    id: Optional[int] = None
    task_id: int
    task_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "running"
    result: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
