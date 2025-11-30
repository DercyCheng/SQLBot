import { request } from '@/utils/request'

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

const buildQueryString = (params?: Record<string, any>): string => {
  if (!params) return ''
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })
  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

export const schedulerApi = {
  // Get paginated scheduled tasks
  getTasks: (currentPage: number, pageSize: number, params?: { name?: string; task_type?: string; status?: string }) =>
    request.get(`/system/scheduler/tasks/page/${currentPage}/${pageSize}${buildQueryString(params)}`),

  // Get task detail
  getTask: (taskId: number) => request.get(`/system/scheduler/tasks/${taskId}`),

  // Create task
  createTask: (data: ScheduledTaskInfo) => request.post('/system/scheduler/tasks', data),

  // Update task
  updateTask: (taskId: number, data: ScheduledTaskInfo) => request.put(`/system/scheduler/tasks/${taskId}`, data),

  // Delete tasks
  deleteTasks: (taskIds: number[]) => request.post('/system/scheduler/tasks/batch-delete', taskIds),

  // Toggle task enabled
  toggleEnabled: (taskId: number, enabled: boolean) => request.post(`/system/scheduler/tasks/${taskId}/enable/${enabled}`),

  // Run task immediately
  runNow: (taskId: number) => request.post(`/system/scheduler/tasks/${taskId}/run`),

  // Get task logs
  getLogs: (currentPage: number, pageSize: number, params?: { task_id?: number; status?: string }) =>
    request.get(`/system/scheduler/logs/page/${currentPage}/${pageSize}${buildQueryString(params)}`),

  // Get scheduler status
  getStatus: () => request.get('/system/scheduler/status'),
}
