<template>
  <div class="scheduler-container">
    <div class="header">
      <div class="title">{{ $t('scheduler.title') }}</div>
      <div class="actions">
        <el-input
          v-model="searchName"
          :placeholder="$t('scheduler.search_task')"
          style="width: 200px; margin-right: 12px"
          clearable
          @clear="loadTasks"
          @keyup.enter="loadTasks"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          {{ $t('scheduler.create_task') }}
        </el-button>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="taskList"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" :label="$t('scheduler.task_name')" min-width="150" />
      <el-table-column prop="task_type" :label="$t('scheduler.task_type')" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ getTaskTypeLabel(row.task_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="action_type" :label="$t('scheduler.action_type')" width="120">
        <template #default="{ row }">
          <el-tag size="small" type="info">{{ getActionTypeLabel(row.action_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" :label="$t('scheduler.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enabled" :label="$t('scheduler.enabled')" width="100">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="toggleEnabled(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="last_run_time" :label="$t('scheduler.last_run_time')" width="180">
        <template #default="{ row }">
          {{ formatTime(row.last_run_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="next_run_time" :label="$t('scheduler.next_run_time')" width="180">
        <template #default="{ row }">
          {{ formatTime(row.next_run_time) }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.operation')" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="runNow(row)">
            {{ $t('scheduler.run_now') }}
          </el-button>
          <el-button link type="primary" @click="openEditDialog(row)">
            {{ $t('common.edit') }}
          </el-button>
          <el-button link type="danger" @click="deleteTask(row)">
            {{ $t('common.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="totalCount"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadTasks"
        @current-change="loadTasks"
      />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? $t('scheduler.edit_task') : $t('scheduler.create_task')"
      width="600px"
    >
      <el-form ref="formRef" :model="taskForm" :rules="formRules" label-width="120px">
        <el-form-item :label="$t('scheduler.task_name')" prop="name">
          <el-input v-model="taskForm.name" />
        </el-form-item>
        <el-form-item :label="$t('scheduler.task_description')">
          <el-input v-model="taskForm.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item :label="$t('scheduler.task_type')" prop="task_type">
          <el-radio-group v-model="taskForm.task_type">
            <el-radio value="cron">{{ $t('scheduler.cron') }}</el-radio>
            <el-radio value="interval">{{ $t('scheduler.interval') }}</el-radio>
            <el-radio value="date">{{ $t('scheduler.date') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="taskForm.task_type === 'cron'" :label="$t('scheduler.cron_expression')" prop="cron_expression">
          <el-input v-model="taskForm.cron_expression" placeholder="*/5 * * * *" />
        </el-form-item>
        <el-form-item v-if="taskForm.task_type === 'interval'" :label="$t('scheduler.interval_seconds')" prop="interval_seconds">
          <el-input-number v-model="taskForm.interval_seconds" :min="1" />
        </el-form-item>
        <el-form-item v-if="taskForm.task_type === 'date'" :label="$t('scheduler.scheduled_date')" prop="scheduled_date">
          <el-date-picker
            v-model="taskForm.scheduled_date"
            type="datetime"
            placeholder="Select date and time"
          />
        </el-form-item>
        <el-form-item :label="$t('scheduler.action_type')" prop="action_type">
          <el-select v-model="taskForm.action_type" style="width: 100%">
            <el-option value="http_request" :label="$t('scheduler.http_request')" />
            <el-option value="sql_query" :label="$t('scheduler.sql_query')" />
            <el-option value="python_script" :label="$t('scheduler.python_script')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('scheduler.action_config')">
          <el-input
            v-model="actionConfigJson"
            type="textarea"
            rows="4"
            placeholder='{"url": "https://example.com", "method": "GET"}'
          />
        </el-form-item>
        <el-form-item :label="$t('scheduler.max_retries')">
          <el-input-number v-model="taskForm.max_retries" :min="0" :max="10" />
        </el-form-item>
        <el-form-item :label="$t('scheduler.retry_delay')">
          <el-input-number v-model="taskForm.retry_delay" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { schedulerApi, type ScheduledTaskInfo } from '@/api/scheduler'

const { t } = useI18n()

// State
const loading = ref(false)
const taskList = ref<ScheduledTaskInfo[]>([])
const selectedTasks = ref<ScheduledTaskInfo[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const searchName = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const taskForm = reactive<ScheduledTaskInfo>({
  name: '',
  description: '',
  task_type: 'cron',
  cron_expression: '',
  interval_seconds: 60,
  scheduled_date: '',
  action_type: 'http_request',
  action_config: {},
  enabled: true,
  max_retries: 3,
  retry_delay: 60
})

const actionConfigJson = ref('')

const formRules = {
  name: [{ required: true, message: t('common.please_input', { msg: t('scheduler.task_name') }), trigger: 'blur' }],
  task_type: [{ required: true, trigger: 'change' }],
  action_type: [{ required: true, trigger: 'change' }]
}

// Methods
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await schedulerApi.getTasks(currentPage.value, pageSize.value, {
      name: searchName.value || undefined
    })
    taskList.value = res.data?.data || []
    totalCount.value = res.data?.total_count || 0
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection: ScheduledTaskInfo[]) => {
  selectedTasks.value = selection
}

const getTaskTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    cron: t('scheduler.cron'),
    interval: t('scheduler.interval'),
    date: t('scheduler.date')
  }
  return labels[type] || type
}

const getActionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    http_request: t('scheduler.http_request'),
    sql_query: t('scheduler.sql_query'),
    python_script: t('scheduler.python_script')
  }
  return labels[type] || type
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    paused: 'info'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: t('scheduler.pending'),
    running: t('scheduler.running'),
    success: t('scheduler.success'),
    failed: t('scheduler.failed'),
    paused: t('scheduler.paused')
  }
  return labels[status] || status
}

const formatTime = (time: string | undefined) => {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

const openCreateDialog = () => {
  isEdit.value = false
  Object.assign(taskForm, {
    id: undefined,
    name: '',
    description: '',
    task_type: 'cron',
    cron_expression: '',
    interval_seconds: 60,
    scheduled_date: '',
    action_type: 'http_request',
    action_config: {},
    enabled: true,
    max_retries: 3,
    retry_delay: 60
  })
  actionConfigJson.value = '{}'
  dialogVisible.value = true
}

const openEditDialog = (task: ScheduledTaskInfo) => {
  isEdit.value = true
  Object.assign(taskForm, task)
  actionConfigJson.value = JSON.stringify(task.action_config || {}, null, 2)
  dialogVisible.value = true
}

const submitForm = async () => {
  await formRef.value?.validate()
  
  try {
    taskForm.action_config = JSON.parse(actionConfigJson.value)
  } catch {
    ElMessage.error('Invalid JSON in action config')
    return
  }

  if (isEdit.value && taskForm.id) {
    await schedulerApi.updateTask(taskForm.id, taskForm)
    ElMessage.success(t('common.update_success'))
  } else {
    await schedulerApi.createTask(taskForm)
    ElMessage.success(t('common.save_success'))
  }
  dialogVisible.value = false
  loadTasks()
}

const toggleEnabled = async (task: ScheduledTaskInfo) => {
  if (task.id) {
    await schedulerApi.toggleEnabled(task.id, task.enabled!)
  }
}

const runNow = async (task: ScheduledTaskInfo) => {
  await ElMessageBox.confirm(
    t('scheduler.confirm_run', { msg: task.name }),
    t('common.confirm')
  )
  if (task.id) {
    await schedulerApi.runNow(task.id)
    ElMessage.success('Task execution triggered')
    loadTasks()
  }
}

const deleteTask = async (task: ScheduledTaskInfo) => {
  await ElMessageBox.confirm(
    t('scheduler.confirm_delete', { msg: '1' }),
    t('common.confirm')
  )
  if (task.id) {
    await schedulerApi.deleteTasks([task.id])
    ElMessage.success(t('dashboard.delete_success'))
    loadTasks()
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped lang="less">
.scheduler-container {
  padding: 20px;
  height: 100%;
  overflow: auto;

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .title {
      font-size: 18px;
      font-weight: 600;
    }

    .actions {
      display: flex;
      align-items: center;
    }
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>
