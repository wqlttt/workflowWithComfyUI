import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export function getObjectInfo() {
  return api.get('/comfyui/object_info')
}

export function queuePrompt(workflow) {
  return api.post('/comfyui/prompt', { prompt: workflow })
}

export function getHistory(promptId) {
  return api.get(`/comfyui/history/${promptId}`)
}

export function getImageUrl(filename, subfolder = '', type = 'output') {
  const params = new URLSearchParams({ filename, subfolder, type })
  return `/api/comfyui/view?${params}`
}

export function uploadImage(file) {
  const form = new FormData()
  form.append('image', file)
  return api.post('/comfyui/upload/image', form)
}

export function getQueue() {
  return api.get('/comfyui/queue')
}

export function clearQueue() {
  return api.delete('/comfyui/queue')
}

export function listWorkflows() {
  return api.get('/workflows')
}

export function saveWorkflow(data) {
  return api.post('/workflows', data)
}

export function loadWorkflow(id) {
  return api.get(`/workflows/${id}`)
}

export function deleteWorkflow(id) {
  return api.delete(`/workflows/${id}`)
}

export function createWebSocket(promptId) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return new WebSocket(`${protocol}//${location.host}/ws/progress/${promptId}`)
}

// SSH Tunnel
export function tunnelConnect(config) {
  return api.post('/tunnel/connect', config)
}
export function tunnelDisconnect() {
  return api.post('/tunnel/disconnect')
}
export function tunnelStatus() {
  return api.get('/tunnel/status')
}

// Server status
export function getGpuStatus() {
  return api.get('/server/gpu')
}
