import { defineStore } from 'pinia'
import { ref } from 'vue'
import { NODE_DEFINITIONS, nextNodeId, graphToPrompt } from '../utils/nodeDefinitions.js'
import { queuePrompt, createWebSocket, getImageUrl } from '../api/index.js'

export const useWorkflowStore = defineStore('workflow', () => {
  const nodes = ref([])
  const edges = ref([])
  const selectedNodeId = ref(null)
  const executionStatus = ref('idle')
  const executionProgress = ref('')
  const generatedImages = ref([])

  const selectedNode = () => {
    return nodes.value.find(n => n.id === selectedNodeId.value)
  }

  function addNode(type, position) {
    const def = NODE_DEFINITIONS[type]
    if (!def) return
    const id = `node-${nextNodeId()}`
    nodes.value.push({
      id,
      type: 'custom',
      position,
      data: {
        type,
        label: def.label,
        params: { ...def.defaults },
        inputs: def.inputs,
        outputs: def.outputs,
      },
    })
  }

  function updateNodeParam(nodeId, key, value) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node && node.data.params) {
      node.data.params[key] = value
      nodes.value = [...nodes.value]
    }
  }

  function removeNode(nodeId) {
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    if (selectedNodeId.value === nodeId) selectedNodeId.value = null
  }

  async function executeWorkflow() {
    try {
      executionStatus.value = 'running'
      executionProgress.value = '构建工作流...'
      generatedImages.value = []

      const prompt = graphToPrompt(nodes.value, edges.value)
      const resp = await queuePrompt(prompt)
      const promptId = resp.data.prompt_id

      executionProgress.value = `已加入队列: ${promptId}`

      const ws = createWebSocket(promptId)
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.status === 'completed') {
          executionStatus.value = 'completed'
          executionProgress.value = '完成!'
          for (const [nodeId, output] of Object.entries(msg.data.outputs || {})) {
            if (output.images) {
              for (const img of output.images) {
                generatedImages.value.push(
                  getImageUrl(img.filename, img.subfolder || '', img.type || 'output')
                )
              }
            }
          }
        } else if (msg.status === 'progress') {
          executionProgress.value = `队列位置: ${msg.queue_position ?? '执行中'}`
        } else if (msg.status === 'error') {
          executionStatus.value = 'error'
          executionProgress.value = msg.message
        }
      }
      ws.onerror = () => {
        executionStatus.value = 'error'
        executionProgress.value = '连接错误'
      }
    } catch (e) {
      executionStatus.value = 'error'
      executionProgress.value = e.message || '执行失败'
    }
  }

  function clearCanvas() {
    nodes.value = []
    edges.value = []
    selectedNodeId.value = null
    executionStatus.value = 'idle'
    executionProgress.value = ''
    generatedImages.value = []
  }

  function loadWorkflowData(data) {
    nodes.value = data.nodes || []
    edges.value = data.edges || []
  }

  return {
    nodes, edges, selectedNodeId, executionStatus, executionProgress,
    generatedImages,
    selectedNode, addNode, updateNodeParam, removeNode, executeWorkflow,
    clearCanvas, loadWorkflowData,
  }
})
