import request from '@/utils/request'

// ==================== Scheduled Task APIs ====================

export interface ScheduledTaskInfo {
    id?: number
    name: string
    description?: string
    task_type: string // 'cron' | 'interval' | 'date'
    cron_expression?: string
    interval_seconds?: number
    scheduled_date?: string
    action_type: string // 'http_request' | 'sql_query' | 'python_script'
    action_config?: Record<string, any>
    enabled?: boolean
    max_retries?: number
    retry_delay?: number
    status?: string
    last_run_time?: string
    next_run_time?: string
    create_time?: string
    update_time?: string
}

export interface TaskLogInfo {
    id?: number
    task_id: number
    task_name?: string
    start_time?: string
    end_time?: string
    duration_ms?: number
    status: string
    result?: string
    error_message?: string
    retry_count?: number
}

// Get paginated scheduled tasks
export const getScheduledTasks = (
    currentPage: number,
    pageSize: number,
    params?: {
        name?: string
        task_type?: string
        status?: string
    }
) => {
    return request({
        url: `/api/v1/system/scheduler/tasks/page/${currentPage}/${pageSize}`,
        method: 'get',
        params
    })
}

// Get task detail
export const getScheduledTask = (taskId: number) => {
    return request({
        url: `/api/v1/system/scheduler/tasks/${taskId}`,
        method: 'get'
    })
}

// Create task
export const createScheduledTask = (data: ScheduledTaskInfo) => {
    return request({
        url: '/api/v1/system/scheduler/tasks',
        method: 'post',
        data
    })
}

// Update task
export const updateScheduledTask = (taskId: number, data: ScheduledTaskInfo) => {
    return request({
        url: `/api/v1/system/scheduler/tasks/${taskId}`,
        method: 'put',
        data
    })
}

// Delete tasks
export const deleteScheduledTasks = (taskIds: number[]) => {
    return request({
        url: '/api/v1/system/scheduler/tasks',
        method: 'delete',
        data: taskIds
    })
}

// Toggle task enabled
export const toggleTaskEnabled = (taskId: number, enabled: boolean) => {
    return request({
        url: `/api/v1/system/scheduler/tasks/${taskId}/enable/${enabled}`,
        method: 'post'
    })
}

// Run task immediately
export const runTaskNow = (taskId: number) => {
    return request({
        url: `/api/v1/system/scheduler/tasks/${taskId}/run`,
        method: 'post'
    })
}

// Get task logs
export const getTaskLogs = (
    currentPage: number,
    pageSize: number,
    params?: {
        task_id?: number
        status?: string
    }
) => {
    return request({
        url: `/api/v1/system/scheduler/logs/page/${currentPage}/${pageSize}`,
        method: 'get',
        params
    })
}

// Get scheduler status
export const getSchedulerStatus = () => {
    return request({
        url: '/api/v1/system/scheduler/status',
        method: 'get'
    })
}
