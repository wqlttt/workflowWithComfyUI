// 三节点架构: 输入 → ComfyUI → 输出

let nodeIdCounter = 1
export function nextNodeId() {
  return nodeIdCounter++
}

export const NODE_DEFINITIONS = {
  InputNode: {
    label: '输入',
    category: 'input',
    inputs: [],
    outputs: [{ key: 'PARAMS' }],
    defaults: {
      type: 'text2image',
      prompt: '',
      negative_prompt: '',
      seed: -1,
      width: 512,
      height: 512,
      batch_size: 1,
    },
  },
  ComfyUINode: {
    label: 'ComfyUI',
    category: 'core',
    inputs: [{ key: 'params' }],
    outputs: [{ key: 'RESULT' }],
    defaults: {
      workflow_json: '',
    },
  },
  OutputNode: {
    label: '输出',
    category: 'output',
    inputs: [{ key: 'result' }],
    outputs: [],
    defaults: {},
  },
}

// 收集所有入口参数（从所有 InputNode 合并）
function collectInputParams(nodes) {
  const params = {}
  for (const node of nodes) {
    if (node.data.type === 'InputNode' && node.data.params) {
      Object.assign(params, node.data.params)
    }
  }
  // seed 随机
  if (params.seed === -1 || params.seed === undefined) {
    params.seed = Math.floor(Math.random() * 999999999999)
  }
  return params
}

// 将输入参数注入 workflow JSON 模板
function injectParams(workflowJson, params) {
  // 深拷贝
  const injected = JSON.parse(JSON.stringify(workflowJson))
  // 遍历所有节点，替换 {{param}} 占位符
  const jsonStr = JSON.stringify(injected)
  const replaced = jsonStr.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    if (params[key] !== undefined) {
      return String(params[key])
    }
    return match
  })
  return JSON.parse(replaced)
}

// 将前端图转为 ComfyUI prompt 格式
export function graphToPrompt(nodes, edges) {
  // 找到 ComfyUINode
  const comfyNode = nodes.find(n => n.data.type === 'ComfyUINode')
  if (!comfyNode) {
    throw new Error('缺少 ComfyUI 节点')
  }

  const workflowJson = comfyNode.data.params?.workflow_json
  if (!workflowJson || typeof workflowJson !== 'object') {
    throw new Error('ComfyUI 节点未配置工作流 JSON')
  }

  // 收集输入参数
  const params = collectInputParams(nodes)

  // 注入参数
  const prompt = injectParams(workflowJson, params)
  return prompt
}
