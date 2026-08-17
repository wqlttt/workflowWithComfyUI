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

// AI 流式提示词生成（SSE，支持多提供商）
export async function generatePrompt(config, onChunk, onError) {
  try {
    const resp = await fetch('/api/ai/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    if (!resp.ok || !resp.body) {
      throw new Error('请求失败: ' + resp.status)
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let full = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        const data = trimmed.slice(6)
        if (data === '[DONE]') return full
        try {
          const json = JSON.parse(data)
          if (json.error) {
            onError && onError(json.error)
            return full
          }
          const d = json.choices?.[0]?.delta
          // 只取最终结果 content，忽略 reasoning_content（思考过程）
          const chunk = d?.content
          if (chunk) {
            full += chunk
            onChunk && onChunk(full)
          }
        } catch {}
      }
    }
    return full
  } catch (e) {
    onError && onError(e.message)
    return ''
  }
}

// AI 提供商管理
export function getAiProviders() {
  return api.get('/ai/providers')
}
export function addAiProvider(data) {
  return api.post('/ai/providers', data)
}
export function updateAiProvider(name, data) {
  return api.put(`/ai/providers/${name}`, data)
}
export function deleteAiProvider(name) {
  return api.delete(`/ai/providers/${name}`)
}
export function testAiProvider(name) {
  return api.post(`/ai/providers/${name}/test`)
}
export function addAiModel(name, model) {
  return api.post(`/ai/providers/${name}/models`, { name: model })
}
export function deleteAiModel(name, model) {
  return api.delete(`/ai/providers/${name}/models/${model}`)
}

// 图像生成（llmgateway Gemini）
export function generateImage(data) {
  return api.post('/image/generate', data)
}
export function getImageConfig() {
  return api.get('/image/config')
}
export function setImageConfig(data) {
  return api.post('/image/config', data)
}

// 项目快照保存/加载
export function saveProject(data) {
  return api.post('/project/save', data)
}
export function loadProject() {
  return api.get('/project/load')
}
