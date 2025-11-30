import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from apps.scheduler.crud.scheduler_crud import (
    create_scheduled_task, update_scheduled_task, delete_scheduled_task,
    get_scheduled_task, page_scheduled_tasks, enable_scheduled_task,
    page_task_logs
)
from apps.scheduler.models.scheduler_model import ScheduledTaskInfo
from apps.scheduler.service.scheduler_service import scheduler_service
from common.core.deps import SessionDep, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scheduler"], prefix="/system/scheduler")


@router.get("/tasks/page/{current_page}/{page_size}")
async def get_tasks_page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
    name: Optional[str] = Query(None, description="Task name filter"),
    task_type: Optional[str] = Query(None, description="Task type filter"),
    status: Optional[str] = Query(None, description="Task status filter")
):
    """Get paginated scheduled tasks"""
    current_page, page_size, total_count, total_pages, tasks = page_scheduled_tasks(
        session, current_page, page_size, current_user.oid, name, task_type, status
    )
    
    return {
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "task_type": t.task_type,
                "cron_expression": t.cron_expression,
                "interval_seconds": t.interval_seconds,
                "scheduled_date": t.scheduled_date,
                "action_type": t.action_type,
                "action_config": t.action_config,
                "enabled": t.enabled,
                "status": t.status,
                "max_retries": t.max_retries,
                "retry_delay": t.retry_delay,
                "last_run_time": t.last_run_time,
                "next_run_time": t.next_run_time,
                "create_time": t.create_time,
                "update_time": t.update_time
            }
            for t in tasks
        ]
    }


@router.get("/tasks/{task_id}")
async def get_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: int
):
    """Get a scheduled task by ID"""
    task = get_scheduled_task(session, task_id, current_user.oid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "task_type": task.task_type,
        "cron_expression": task.cron_expression,
        "interval_seconds": task.interval_seconds,
        "scheduled_date": task.scheduled_date,
        "action_type": task.action_type,
        "action_config": task.action_config,
        "enabled": task.enabled,
        "status": task.status,
        "max_retries": task.max_retries,
        "retry_delay": task.retry_delay,
        "last_run_time": task.last_run_time,
        "next_run_time": task.next_run_time,
        "create_time": task.create_time,
        "update_time": task.update_time
    }


@router.post("/tasks")
async def create_task(
    session: SessionDep,
    current_user: CurrentUser,
    info: ScheduledTaskInfo
):
    """Create a new scheduled task"""
    task = create_scheduled_task(session, info, current_user.oid, current_user.id)
    
    # Register with scheduler service
    if task.enabled:
        scheduler_service.add_task(task)
    
    return {"id": task.id, "message": "Task created successfully"}


@router.put("/tasks/{task_id}")
async def update_task(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: int,
    info: ScheduledTaskInfo
):
    """Update an existing scheduled task"""
    task = update_scheduled_task(session, task_id, info, current_user.oid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update scheduler
    scheduler_service.remove_task(task_id)
    if task.enabled:
        scheduler_service.add_task(task)
    
    return {"id": task.id, "message": "Task updated successfully"}


@router.delete("/tasks")
async def delete_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    task_ids: list[int]
):
    """Delete scheduled tasks"""
    # Remove from scheduler
    for task_id in task_ids:
        scheduler_service.remove_task(task_id)
    
    count = delete_scheduled_task(session, task_ids, current_user.oid)
    return {"deleted": count, "message": f"Deleted {count} tasks"}


@router.post("/tasks/batch-delete")
async def batch_delete_tasks(
    session: SessionDep,
    current_user: CurrentUser,
    task_ids: list[int]
):
    """Batch delete scheduled tasks (POST method for frontend compatibility)"""
    # Remove from scheduler
    for task_id in task_ids:
        scheduler_service.remove_task(task_id)
    
    count = delete_scheduled_task(session, task_ids, current_user.oid)
    return {"deleted": count, "message": f"Deleted {count} tasks"}


@router.post("/tasks/{task_id}/enable/{enabled}")
async def toggle_task_enabled(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: int,
    enabled: bool
):
    """Enable or disable a scheduled task"""
    success = enable_scheduled_task(session, task_id, enabled, current_user.oid)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update scheduler
    task = get_scheduled_task(session, task_id, current_user.oid)
    if task:
        if enabled:
            scheduler_service.add_task(task)
        else:
            scheduler_service.remove_task(task_id)
    
    return {"message": f"Task {'enabled' if enabled else 'disabled'} successfully"}


@router.post("/tasks/{task_id}/run")
async def run_task_now(
    session: SessionDep,
    current_user: CurrentUser,
    task_id: int
):
    """Run a task immediately"""
    task = get_scheduled_task(session, task_id, current_user.oid)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Execute task immediately
    scheduler_service.run_task_now(task, session)
    
    return {"message": "Task execution triggered"}


@router.get("/logs/page/{current_page}/{page_size}")
async def get_logs_page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get paginated task execution logs"""
    current_page, page_size, total_count, total_pages, logs = page_task_logs(
        session, current_page, page_size, current_user.oid, task_id, status
    )
    
    return {
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": logs
    }


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler service status"""
    return {
        "running": scheduler_service.is_running(),
        "job_count": scheduler_service.get_job_count()
    }
