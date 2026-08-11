<script setup>
import { ref, onUnmounted } from 'vue'
import { useWorkflowStore } from '../stores/workflow.js'
import { saveWorkflow, listWorkflows, loadWorkflow, tunnelConnect, tunnelDisconnect, getGpuStatus } from '../api/index.js'

const props = defineProps({
  showNodePanel: Boolean,
  showPropertyPanel: Boolean,
})
const emit = defineEmits(['update:showNodePanel', 'update:showPropertyPanel'])

const store = useWorkflowStore()

// SSH 隧道
const sshConnected = ref(false)
const sshConnecting = ref(false)
const showSshDialog = ref(false)
const sshConfig = ref({
  host: '', port: 22, username: 'root', password: '', remote_port: 8188, local_port: 8189,
})

// GPU 状态
const showGpuPanel = ref(false)
const gpuList = ref([])
let gpuTimer = null

// 通用
const showSaveDialog = ref(false)
const showLoadDialog = ref(false)
const workflowName = ref('')
const savedWorkflows = ref([])
const message = ref('')

// 加载保存的 SSH 配置
try {
  const saved = localStorage.getItem('sshConfig')
  if (saved) sshConfig.value = { ...sshConfig.value, ...JSON.parse(saved) }
} catch {}

async function toggleSsh() {
  if (sshConnected.value) {
    await tunnelDisconnect()
    sshConnected.value = false
    stopGpuPolling()
    message.value = 'SSH 已断开'
  } else {
    showSshDialog.value = true
  }
}

async function connectSsh() {
  sshConnecting.value = true
  try {
    localStorage.setItem('sshConfig', JSON.stringify(sshConfig.value))
    await tunnelConnect(sshConfig.value)
    sshConnected.value = true
    showSshDialog.value = false
    startGpuPolling()
    message.value = 'SSH 已连接'
  } catch (e) {
    message.value = '连接失败: ' + (e.response?.data?.error || e.message)
  } finally {
    sshConnecting.value = false
  }
  setTimeout(() => message.value = '', 3000)
}

async function fetchGpuStatus() {
  try {
    const resp = await getGpuStatus()
    if (resp.data.ok) gpuList.value = resp.data.gpus
  } catch {}
}

function startGpuPolling() {
  showGpuPanel.value = true
  fetchGpuStatus()
  gpuTimer = setInterval(fetchGpuStatus, 5000)
}

function stopGpuPolling() {
  showGpuPanel.value = false
  if (gpuTimer) { clearInterval(gpuTimer); gpuTimer = null }
  gpuList.value = []
}

onUnmounted(() => stopGpuPolling())

// 保存/加载
async function saveWorkflowHandler() {
  try {
    const data = { name: workflowName.value || '未命名', nodes: store.nodes, edges: store.edges }
    await saveWorkflow(data)
    showSaveDialog.value = false
    message.value = '已保存'
    setTimeout(() => message.value = '', 2000)
  } catch (e) { message.value = '保存失败: ' + e.message }
}

async function openLoadDialog() {
  try {
    const resp = await listWorkflows()
    savedWorkflows.value = resp.data
    showLoadDialog.value = true
  } catch (e) { message.value = '加载列表失败' }
}

async function loadWorkflowHandler(id) {
  try {
    const resp = await loadWorkflow(id)
    store.loadWorkflowData(resp.data)
    showLoadDialog.value = false
    message.value = '已加载'
    setTimeout(() => message.value = '', 2000)
  } catch (e) { message.value = '加载失败: ' + e.message }
}
</script>

<template>
  <div class="toolbar">
    <div class="tb-left">
      <button @click="emit('update:showNodePanel', !showNodePanel)" :class="{ active: showNodePanel }">节点</button>
      <button @click="emit('update:showPropertyPanel', !showPropertyPanel)" :class="{ active: showPropertyPanel }">属性</button>
      <span class="sep">|</span>
      <button class="primary" @click="store.executeWorkflow()" :disabled="store.executionStatus === 'running'">
        {{ store.executionStatus === 'running' ? '运行中...' : '执行' }}
      </button>
    </div>

    <div class="tb-center">
      <span v-if="store.executionProgress" class="progress">{{ store.executionProgress }}</span>
      <span v-if="message" class="msg">{{ message }}</span>
    </div>

    <div class="tb-right">
      <button @click="toggleSsh" :class="{ ssh: sshConnected }" :title="sshConnected ? '断开 SSH' : '连接 SSH'">
        {{ sshConnected ? 'SSH ✓' : 'SSH' }}
      </button>
      <span class="sep">|</span>
      <button @click="openLoadDialog">加载</button>
      <button @click="showSaveDialog = true">保存</button>
      <button @click="store.clearCanvas()">清空</button>
    </div>

    <!-- SSH 连接弹窗 -->
    <div v-if="showSshDialog" class="modal-overlay" @click.self="showSshDialog = false">
      <div class="modal">
        <h3>SSH 连接 AutoDL</h3>
        <div class="ssh-grid">
          <div class="ssh-field">
            <label>主机地址</label>
            <input v-model="sshConfig.host" placeholder="region.autodl.com" />
          </div>
          <div class="ssh-field">
            <label>端口</label>
            <input type="number" v-model.number="sshConfig.port" />
          </div>
          <div class="ssh-field">
            <label>用户名</label>
            <input v-model="sshConfig.username" />
          </div>
          <div class="ssh-field">
            <label>密码</label>
            <input type="password" v-model="sshConfig.password" />
          </div>
          <div class="ssh-field">
            <label>ComfyUI 端口</label>
            <input type="number" v-model.number="sshConfig.remote_port" />
          </div>
          <div class="ssh-field">
            <label>本地转发端口</label>
            <input type="number" v-model.number="sshConfig.local_port" />
          </div>
        </div>
        <div class="modal-actions">
          <button @click="connectSsh" :disabled="sshConnecting">
            {{ sshConnecting ? '连接中...' : '连接' }}
          </button>
          <button @click="showSshDialog = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 保存弹窗 -->
    <div v-if="showSaveDialog" class="modal-overlay" @click.self="showSaveDialog = false">
      <div class="modal">
        <h3>保存工作流</h3>
        <label>名称</label>
        <input v-model="workflowName" placeholder="输入工作流名称" />
        <div class="modal-actions">
          <button @click="saveWorkflowHandler">保存</button>
          <button @click="showSaveDialog = false">取消</button>
        </div>
      </div>
    </div>

    <!-- 加载弹窗 -->
    <div v-if="showLoadDialog" class="modal-overlay" @click.self="showLoadDialog = false">
      <div class="modal">
        <h3>加载工作流</h3>
        <div v-if="savedWorkflows.length === 0" class="empty">暂无保存的工作流</div>
        <div v-for="wf in savedWorkflows" :key="wf.id" class="wf-item" @click="loadWorkflowHandler(wf.id)">{{ wf.name }}</div>
        <div class="modal-actions"><button @click="showLoadDialog = false">取消</button></div>
      </div>
    </div>

    <!-- GPU 状态面板 -->
    <div v-if="showGpuPanel && gpuList.length" class="gpu-panel">
      <div class="gpu-title">GPU 状态</div>
      <div v-for="gpu in gpuList" :key="gpu.index" class="gpu-card">
        <div class="gpu-name">{{ gpu.name }}</div>
        <div class="gpu-bars">
          <div class="bar-row">
            <span>GPU</span>
            <div class="bar-bg"><div class="bar-fill gpu" :style="{ width: gpu.gpu_util + '%' }"></div></div>
            <span>{{ gpu.gpu_util }}%</span>
          </div>
          <div class="bar-row">
            <span>显存</span>
            <div class="bar-bg"><div class="bar-fill mem" :style="{ width: (gpu.mem_used / gpu.mem_total * 100) + '%' }"></div></div>
            <span>{{ gpu.mem_used }}/{{ gpu.mem_total }} MB</span>
          </div>
        </div>
        <div class="gpu-info">
          <span>{{ gpu.temp }}°C</span>
          <span>{{ gpu.power }}W</span>
        </div>
      </div>
    </div>

    <!-- 输出图片 -->
    <div v-if="store.generatedImages.length > 0" class="images-panel">
      <div class="images-title">输出</div>
      <div class="images-grid">
        <img v-for="(url, i) in store.generatedImages" :key="i" :src="url" class="output-img" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  height: 40px;
  background: #0f3460;
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 4px;
  position: relative;
}
.toolbar button {
  background: transparent;
  border: 1px solid #1a1a4e;
  color: #ccc;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all .15s;
}
.toolbar button:hover { background: #1a1a4e; color: #fff; }
.toolbar button.active { background: #e94560; border-color: #e94560; color: #fff; }
.toolbar button.primary { background: #e94560; border-color: #e94560; color: #fff; }
.toolbar button.primary:disabled { opacity: 0.5; cursor: not-allowed; }
.toolbar button.primary:hover:not(:disabled) { background: #c73a52; }
.toolbar button.ssh { background: #1a6e1a; border-color: #2a8e2a; color: #fff; }
.sep { color: #555; margin: 0 4px; }
.tb-left, .tb-center, .tb-right { display: flex; align-items: center; gap: 4px; }
.tb-center { flex: 1; justify-content: center; }
.progress { font-size: 12px; color: #66ccff; }
.msg { font-size: 12px; color: #6f6; }

/* modals */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
  padding: 20px; min-width: 360px; max-width: 480px;
}
.modal h3 { margin-bottom: 12px; font-size: 15px; }
.modal label { font-size: 12px; color: #888; display: block; margin-bottom: 2px; }
.modal input { width: 100%; background: #0f3460; border: 1px solid #1a1a4e; color: #eee; padding: 6px 8px; border-radius: 4px; outline: none; font-size: 13px; }
.modal-actions { margin-top: 14px; display: flex; gap: 8px; justify-content: flex-end; }
.modal-actions button { padding: 6px 16px; border-radius: 4px; border: 1px solid #0f3460; background: #0f3460; color: #eee; cursor: pointer; font-size: 12px; }
.modal-actions button:hover { background: #e94560; }
.wf-item { padding: 8px; cursor: pointer; border-radius: 4px; margin: 4px 0; }
.wf-item:hover { background: #0f3460; }
.empty { color: #666; font-size: 13px; padding: 12px 0; }

.ssh-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

/* GPU panel */
.gpu-panel {
  position: fixed; top: 48px; right: 12px;
  background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
  padding: 12px; z-index: 500; min-width: 240px;
}
.gpu-title { font-size: 13px; color: #4fc08d; margin-bottom: 8px; font-weight: 600; }
.gpu-card { margin-bottom: 8px; }
.gpu-name { font-size: 11px; color: #aaa; margin-bottom: 4px; }
.bar-row { display: flex; align-items: center; gap: 4px; font-size: 10px; color: #888; margin: 2px 0; }
.bar-bg { flex: 1; height: 8px; background: #0f3460; border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width .3s; }
.bar-fill.gpu { background: #66ccff; }
.bar-fill.mem { background: #e94560; }
.bar-row span:first-child { width: 28px; }
.bar-row span:last-child { width: 80px; text-align: right; }
.gpu-info { display: flex; gap: 12px; font-size: 10px; color: #666; margin-top: 2px; }

/* Images panel */
.images-panel {
  position: fixed; bottom: 12px; right: 12px;
  background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
  padding: 12px; z-index: 500; max-width: 400px;
}
.images-title { font-size: 13px; color: #e94560; margin-bottom: 8px; }
.images-grid { display: flex; gap: 8px; flex-wrap: wrap; }
.output-img { max-height: 200px; border-radius: 4px; cursor: pointer; }
</style>
