import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { NODE_DEFINITIONS, nextNodeId, graphToPrompt } from '../utils/nodeDefinitions.js'
import {
  queuePrompt, createWebSocket, getImageUrl,
  listProjects, createProject as createProjectApi,
  getProject, updateProject, deleteProject,
} from '../api/index.js'

const AUTOSAVE_KEY = 'workflow_autosave'

export const useWorkflowStore = defineStore('workflow', () => {
  // 从 localStorage 恢复上次状态
  let saved = {}
  try {
    const raw = localStorage.getItem(AUTOSAVE_KEY)
    if (raw) saved = JSON.parse(raw)
  } catch {}

  const view = ref(saved.view || 'home')
  const currentProjectId = ref(saved.currentProjectId || null)
  const currentProjectName = ref(saved.currentProjectName || '')
  const projects = ref([])
  const nodes = ref(saved.nodes || [])
  const edges = ref(saved.edges || [])
  const selectedNodeId = ref(null)
  const executionStatus = ref('idle')
  const executionProgress = ref('')
  const generatedImages = ref(saved.generatedImages || [])

  // 自动保存（防抖 500ms）
  let saveTimer = null
  watch([nodes, edges, view, currentProjectId, currentProjectName, generatedImages], () => {
    clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      try {
        localStorage.setItem(AUTOSAVE_KEY, JSON.stringify({
          view: view.value,
          currentProjectId: currentProjectId.value,
          currentProjectName: currentProjectName.value,
          nodes: nodes.value,
          edges: edges.value,
          generatedImages: generatedImages.value,
        }))
      } catch {}
    }, 500)
  }, { deep: true })

  const selectedNode = () => {
    return nodes.value.find(n => n.id === selectedNodeId.value)
  }

  // ── 项目管理 ──

  async function fetchProjects() {
    try {
      const resp = await listProjects()
      projects.value = resp.data
    } catch {}
  }

  async function createProject(name) {
    try {
      const resp = await createProjectApi({ name: name || '未命名项目' })
      const project = resp.data
      currentProjectId.value = project.id
      currentProjectName.value = project.name
      nodes.value = []
      edges.value = []
      generatedImages.value = []
      selectedNodeId.value = null
      view.value = 'editor'
      return project
    } catch {
      return null
    }
  }

  async function openProject(id) {
    try {
      const resp = await getProject(id)
      const project = resp.data
      currentProjectId.value = project.id
      currentProjectName.value = project.name
      nodes.value = project.nodes || []
      edges.value = project.edges || []
      generatedImages.value = project.generated_images || []
      selectedNodeId.value = null
      view.value = 'editor'
    } catch {}
  }

  async function saveCurrentProject() {
    if (!currentProjectId.value) return false
    try {
      await updateProject(currentProjectId.value, {
        name: currentProjectName.value,
        nodes: nodes.value,
        edges: edges.value,
        generated_images: generatedImages.value,
      })
      return true
    } catch {
      return false
    }
  }

  async function removeProject(id) {
    try {
      await deleteProject(id)
      await fetchProjects()
    } catch {}
  }

  function backToHome() {
    view.value = 'home'
    fetchProjects()
  }

  // ── 节点操作 ──

  function addNode(type, position) {
    const def = NODE_DEFINITIONS[type]
    if (!def) return

    if (type === 'PromptGeneratorNode') {
      const genId = `node-${nextNodeId()}`
      const resultId = `node-${nextNodeId()}`
      nodes.value.push({
        id: genId,
        type: 'custom',
        position,
        data: {
          type,
          label: def.label,
          params: { ...def.defaults, result_node_id: resultId },
          inputs: def.inputs,
          outputs: def.outputs,
        },
      })
      const resultDef = NODE_DEFINITIONS.PromptResultNode
      nodes.value.push({
        id: resultId,
        type: 'custom',
        position: { x: position.x + 300, y: position.y },
        data: {
          type: 'PromptResultNode',
          label: resultDef.label,
          params: { ...resultDef.defaults, parent_generator: genId },
          inputs: resultDef.inputs,
          outputs: resultDef.outputs,
        },
      })
      edges.value.push({
        id: `edge-${genId}-${resultId}`,
        source: genId,
        target: resultId,
        sourceHandle: 'output-0',
        targetHandle: 'input-0',
      })
      return
    }

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

  function updatePromptResult(generatorNodeId, text) {
    const genNode = nodes.value.find(n => n.id === generatorNodeId)
    if (!genNode || !genNode.data.params.result_node_id) return
    const resultNode = nodes.value.find(n => n.id === genNode.data.params.result_node_id)
    if (resultNode && resultNode.data.params) {
      resultNode.data.params.prompt_text = text
      nodes.value = [...nodes.value]
    }
  }

  function removeNode(nodeId) {
    const node = nodes.value.find(n => n.id === nodeId)
    const idsToRemove = [nodeId]
    if (node) {
      if (node.data.type === 'PromptGeneratorNode' && node.data.params.result_node_id) {
        idsToRemove.push(node.data.params.result_node_id)
      } else if (node.data.type === 'PromptResultNode' && node.data.params.parent_generator) {
        idsToRemove.push(node.data.params.parent_generator)
      }
    }
    nodes.value = nodes.value.filter(n => !idsToRemove.includes(n.id))
    edges.value = edges.value.filter(e => !idsToRemove.includes(e.source) && !idsToRemove.includes(e.target))
    if (idsToRemove.includes(selectedNodeId.value)) selectedNodeId.value = null
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
    view, currentProjectId, currentProjectName, projects,
    nodes, edges, selectedNodeId, executionStatus, executionProgress, generatedImages,
    selectedNode, addNode, updateNodeParam, updatePromptResult, removeNode, executeWorkflow,
    clearCanvas, loadWorkflowData,
    fetchProjects, createProject, openProject, saveCurrentProject, removeProject, backToHome,
  }
})
