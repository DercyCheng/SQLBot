import datetime
import logging
from typing import Optional, List, Tuple

from sqlalchemy import select, func, delete, update, and_
from sqlalchemy.orm import Session

from apps.scheduler.models.scheduler_model import (
    ScheduledTask, TaskLog, ScheduledTaskInfo, TaskLogInfo
)
from common.core.deps import SessionDep

logger = logging.getLogger(__name__)


def create_scheduled_task(
    session: SessionDep,
    info: ScheduledTaskInfo,
    oid: int,
    user_id: int
) -> ScheduledTask:
    """Create a new scheduled task"""
    now = datetime.datetime.now()
    
    task = ScheduledTask(
        oid=oid,
        name=info.name,
        description=info.description,
        task_type=info.task_type,
        cron_expression=info.cron_expression,
        interval_seconds=info.interval_seconds,
        scheduled_date=info.scheduled_date,
        action_type=info.action_type,
        action_config=info.action_config or {},
        enabled=info.enabled,
        max_retries=info.max_retries,
        retry_delay=info.retry_delay,
        status="pending",
        create_time=now,
        update_time=now,
        created_by=user_id
    )
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    return task


def update_scheduled_task(
    session: SessionDep,
    task_id: int,
    info: ScheduledTaskInfo,
    oid: int
) -> Optional[ScheduledTask]:
    """Update an existing scheduled task"""
    task = session.get(ScheduledTask, task_id)
    
    if not task or task.oid != oid:
        return None
    
    task.name = info.name
    task.description = info.description
    task.task_type = info.task_type
    task.cron_expression = info.cron_expression
    task.interval_seconds = info.interval_seconds
    task.scheduled_date = info.scheduled_date
    task.action_type = info.action_type
    task.action_config = info.action_config or {}
    task.enabled = info.enabled
    task.max_retries = info.max_retries
    task.retry_delay = info.retry_delay
    task.update_time = datetime.datetime.now()
    
    session.commit()
    session.refresh(task)
    
    return task


def delete_scheduled_task(session: SessionDep, task_ids: List[int], oid: int) -> int:
    """Delete scheduled tasks by IDs"""
    stmt = delete(ScheduledTask).where(
        and_(
            ScheduledTask.id.in_(task_ids),
            ScheduledTask.oid == oid
        )
    )
    result = session.execute(stmt)
    
    # Also delete associated logs
    stmt_logs = delete(TaskLog).where(TaskLog.task_id.in_(task_ids))
    session.execute(stmt_logs)
    
    session.commit()
    return result.rowcount


def get_scheduled_task(session: SessionDep, task_id: int, oid: int) -> Optional[ScheduledTask]:
    """Get a scheduled task by ID"""
    stmt = select(ScheduledTask).where(
        and_(
            ScheduledTask.id == task_id,
            ScheduledTask.oid == oid
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def page_scheduled_tasks(
    session: SessionDep,
    current_page: int,
    page_size: int,
    oid: int,
    name: Optional[str] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None
) -> Tuple[int, int, int, int, List[ScheduledTask]]:
    """Get paginated scheduled tasks"""
    
    # Build filter conditions
    conditions = [ScheduledTask.oid == oid]
    
    if name:
        conditions.append(ScheduledTask.name.ilike(f"%{name}%"))
    if task_type:
        conditions.append(ScheduledTask.task_type == task_type)
    if status:
        conditions.append(ScheduledTask.status == status)
    
    # Count total
    count_stmt = select(func.count()).select_from(ScheduledTask).where(and_(*conditions))
    total_count = session.execute(count_stmt).scalar() or 0
    
    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size
    offset = (current_page - 1) * page_size
    
    # Fetch data
    stmt = (
        select(ScheduledTask)
        .where(and_(*conditions))
        .order_by(ScheduledTask.create_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    tasks = session.execute(stmt).scalars().all()
    
    return current_page, page_size, total_count, total_pages, list(tasks)


def enable_scheduled_task(
    session: SessionDep,
    task_id: int,
    enabled: bool,
    oid: int
) -> bool:
    """Enable or disable a scheduled task"""
    stmt = (
        update(ScheduledTask)
        .where(and_(ScheduledTask.id == task_id, ScheduledTask.oid == oid))
        .values(enabled=enabled, update_time=datetime.datetime.now())
    )
    result = session.execute(stmt)
    session.commit()
    return result.rowcount > 0


def update_task_status(
    session: SessionDep,
    task_id: int,
    status: str,
    last_run_time: Optional[datetime.datetime] = None,
    next_run_time: Optional[datetime.datetime] = None
):
    """Update task status and run times"""
    values = {
        "status": status,
        "update_time": datetime.datetime.now()
    }
    if last_run_time:
        values["last_run_time"] = last_run_time
    if next_run_time:
        values["next_run_time"] = next_run_time
    
    stmt = update(ScheduledTask).where(ScheduledTask.id == task_id).values(**values)
    session.execute(stmt)
    session.commit()


def create_task_log(
    session: SessionDep,
    task_id: int,
    oid: int
) -> TaskLog:
    """Create a new task execution log"""
    log = TaskLog(
        task_id=task_id,
        oid=oid,
        start_time=datetime.datetime.now(),
        status="running",
        retry_count=0
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def update_task_log(
    session: SessionDep,
    log_id: int,
    status: str,
    result: Optional[str] = None,
    error_message: Optional[str] = None,
    retry_count: int = 0
):
    """Update task log with execution result"""
    end_time = datetime.datetime.now()
    
    log = session.get(TaskLog, log_id)
    if log:
        duration_ms = int((end_time - log.start_time).total_seconds() * 1000) if log.start_time else 0
        
        log.end_time = end_time
        log.duration_ms = duration_ms
        log.status = status
        log.result = result
        log.error_message = error_message
        log.retry_count = retry_count
        
        session.commit()


def page_task_logs(
    session: SessionDep,
    current_page: int,
    page_size: int,
    oid: int,
    task_id: Optional[int] = None,
    status: Optional[str] = None
) -> Tuple[int, int, int, int, List[dict]]:
    """Get paginated task logs"""
    
    conditions = [TaskLog.oid == oid]
    
    if task_id:
        conditions.append(TaskLog.task_id == task_id)
    if status:
        conditions.append(TaskLog.status == status)
    
    # Count total
    count_stmt = select(func.count()).select_from(TaskLog).where(and_(*conditions))
    total_count = session.execute(count_stmt).scalar() or 0
    
    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size
    offset = (current_page - 1) * page_size
    
    # Fetch data with task name
    stmt = (
        select(TaskLog, ScheduledTask.name)
        .join(ScheduledTask, TaskLog.task_id == ScheduledTask.id, isouter=True)
        .where(and_(*conditions))
        .order_by(TaskLog.start_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    results = session.execute(stmt).all()
    
    logs = []
    for log, task_name in results:
        log_dict = {
            "id": log.id,
            "task_id": log.task_id,
            "task_name": task_name,
            "start_time": log.start_time,
            "end_time": log.end_time,
            "duration_ms": log.duration_ms,
            "status": log.status,
            "result": log.result,
            "error_message": log.error_message,
            "retry_count": log.retry_count
        }
        logs.append(log_dict)
    
    return current_page, page_size, total_count, total_pages, logs


def get_enabled_tasks(session: SessionDep) -> List[ScheduledTask]:
    """Get all enabled scheduled tasks"""
    stmt = select(ScheduledTask).where(ScheduledTask.enabled == True)
    return list(session.execute(stmt).scalars().all())
