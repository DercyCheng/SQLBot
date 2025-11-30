import datetime
import logging
import traceback
from typing import Optional, Callable, Any
import threading
import httpx
import json

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from apps.scheduler.models.scheduler_model import ScheduledTask
from common.utils.utils import SQLBotLogUtil

logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler service using APScheduler"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._scheduler = BackgroundScheduler(
            timezone='Asia/Shanghai',
            job_defaults={
                'coalesce': True,
                'max_instances': 3,
                'misfire_grace_time': 60
            }
        )
        self._task_sessions = {}  # Store session factories for each task
        self._initialized = True
        
        # Add event listeners
        self._scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
    
    def start(self):
        """Start the scheduler"""
        if not self._scheduler.running:
            self._scheduler.start()
            SQLBotLogUtil.info("✅ Scheduler service started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self._scheduler.running:
            self._scheduler.shutdown()
            SQLBotLogUtil.info("Scheduler service stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._scheduler.running
    
    def get_job_count(self) -> int:
        """Get number of scheduled jobs"""
        return len(self._scheduler.get_jobs())
    
    def add_task(self, task: ScheduledTask):
        """Add a scheduled task to the scheduler"""
        job_id = f"task_{task.id}"
        
        # Remove existing job if any
        self.remove_task(task.id)
        
        # Create trigger based on task type
        trigger = self._create_trigger(task)
        if not trigger:
            logger.error(f"Failed to create trigger for task {task.id}")
            return
        
        # Add job
        self._scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            id=job_id,
            args=[task.id, task.oid, task.action_type, task.action_config, 
                  task.max_retries, task.retry_delay],
            name=task.name,
            replace_existing=True
        )
        
        SQLBotLogUtil.info(f"Added scheduled task: {task.name} (ID: {task.id})")
    
    def remove_task(self, task_id: int):
        """Remove a scheduled task from the scheduler"""
        job_id = f"task_{task_id}"
        try:
            self._scheduler.remove_job(job_id)
            SQLBotLogUtil.info(f"Removed scheduled task ID: {task_id}")
        except Exception:
            pass  # Job doesn't exist
    
    def run_task_now(self, task: ScheduledTask, session):
        """Run a task immediately"""
        try:
            self._execute_task(
                task.id, task.oid, task.action_type, 
                task.action_config, task.max_retries, task.retry_delay
            )
        except Exception as e:
            logger.error(f"Failed to execute task {task.id}: {str(e)}")
            raise
    
    def _create_trigger(self, task: ScheduledTask):
        """Create APScheduler trigger based on task configuration"""
        try:
            if task.task_type == "cron" and task.cron_expression:
                # Parse cron expression (minute hour day month day_of_week)
                parts = task.cron_expression.split()
                if len(parts) >= 5:
                    return CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4]
                    )
            
            elif task.task_type == "interval" and task.interval_seconds:
                return IntervalTrigger(seconds=task.interval_seconds)
            
            elif task.task_type == "date" and task.scheduled_date:
                return DateTrigger(run_date=task.scheduled_date)
            
        except Exception as e:
            logger.error(f"Error creating trigger for task {task.id}: {str(e)}")
        
        return None
    
    def _execute_task(
        self, 
        task_id: int, 
        oid: int, 
        action_type: str, 
        action_config: dict,
        max_retries: int,
        retry_delay: int
    ):
        """Execute a scheduled task"""
        from apps.db.db import engine
        from sqlmodel import Session
        from apps.scheduler.crud.scheduler_crud import (
            create_task_log, update_task_log, update_task_status
        )
        
        SQLBotLogUtil.info(f"Executing task {task_id}")
        
        with Session(engine) as session:
            # Create execution log
            log = create_task_log(session, task_id, oid)
            
            # Update task status
            update_task_status(
                session, task_id, "running",
                last_run_time=datetime.datetime.now()
            )
            
            retry_count = 0
            success = False
            result = None
            error_msg = None
            
            while retry_count <= max_retries and not success:
                try:
                    result = self._run_action(action_type, action_config)
                    success = True
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Task {task_id} failed (attempt {retry_count + 1}): {error_msg}")
                    traceback.print_exc()
                    
                    retry_count += 1
                    if retry_count <= max_retries:
                        import time
                        time.sleep(retry_delay)
            
            # Update log
            update_task_log(
                session, log.id,
                status="success" if success else "failed",
                result=result,
                error_message=error_msg,
                retry_count=retry_count
            )
            
            # Update task status
            update_task_status(
                session, task_id,
                status="success" if success else "failed"
            )
            
            SQLBotLogUtil.info(
                f"Task {task_id} completed: {'success' if success else 'failed'}"
            )
    
    def _run_action(self, action_type: str, config: dict) -> str:
        """Run the configured action"""
        if action_type == "http_request":
            return self._run_http_request(config)
        elif action_type == "sql_query":
            return self._run_sql_query(config)
        elif action_type == "python_script":
            return self._run_python_script(config)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _run_http_request(self, config: dict) -> str:
        """Execute HTTP request action"""
        url = config.get("url")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        body = config.get("body")
        timeout = config.get("timeout", 30)
        
        with httpx.Client(timeout=timeout) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=body)
            elif method == "PUT":
                response = client.put(url, headers=headers, json=body)
            elif method == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return f"Status: {response.status_code}, Response: {response.text[:500]}"
    
    def _run_sql_query(self, config: dict) -> str:
        """Execute SQL query action"""
        from apps.datasource.curd.datasource import get_datasource_by_id
        from apps.db.db import engine
        from apps.db.engine import get_engine_by_datasource
        from sqlmodel import Session
        
        datasource_id = config.get("datasource_id")
        sql = config.get("sql")
        
        with Session(engine) as session:
            ds = get_datasource_by_id(session, datasource_id)
            if not ds:
                raise ValueError(f"Datasource {datasource_id} not found")
            
            ds_engine = get_engine_by_datasource(ds)
            with ds_engine.connect() as conn:
                result = conn.execute(sql)
                rows = result.fetchall() if result.returns_rows else []
                return f"Executed successfully. Rows affected/returned: {len(rows)}"
    
    def _run_python_script(self, config: dict) -> str:
        """Execute Python script action (sandboxed)"""
        script = config.get("script", "")
        
        # Create a restricted execution environment
        allowed_imports = {"datetime", "json", "math", "re"}
        exec_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "abs": abs,
                "round": round,
            }
        }
        
        # Add allowed modules
        import datetime
        import json
        import math
        import re
        
        exec_globals["datetime"] = datetime
        exec_globals["json"] = json
        exec_globals["math"] = math
        exec_globals["re"] = re
        
        exec_locals = {}
        
        exec(script, exec_globals, exec_locals)
        
        result = exec_locals.get("result", "Script executed successfully")
        return str(result)
    
    def _job_executed_listener(self, event):
        """Listener for job execution events"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed with exception")
        else:
            logger.info(f"Job {event.job_id} executed successfully")
    
    def load_tasks_from_db(self):
        """Load all enabled tasks from database"""
        from apps.db.db import engine
        from sqlmodel import Session
        from apps.scheduler.crud.scheduler_crud import get_enabled_tasks
        
        with Session(engine) as session:
            tasks = get_enabled_tasks(session)
            for task in tasks:
                self.add_task(task)
            
            SQLBotLogUtil.info(f"Loaded {len(tasks)} scheduled tasks from database")


# Singleton instance
scheduler_service = SchedulerService()
