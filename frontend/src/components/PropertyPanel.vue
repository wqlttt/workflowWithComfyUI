<script setup>
import { ref, onMounted, computed } from 'vue'
import { useWorkflowStore } from '../stores/workflow.js'
import { generatePrompt, getAiProviders, generateImage } from '../api/index.js'

const store = useWorkflowStore()

const typeOptions = [
  { value: 'text2image', label: '文生图' },
  { value: 'text2video', label: '文生视频' },
  { value: 'img2img', label: '图生图' },
]

const generating = ref(false)
const genError = ref('')
const aiProviders = ref([])
const copied = ref(false)
const generatingImage = ref(false)
const imgError = ref('')

// 生图：优先取连线来的提示词，否则用节点自身的 prompt
function resolveImagePrompt(node) {
  const edge = store.edges.find(e => e.target === node.id && e.targetHandle === 'input-0')
  if (edge) {
    const src = store.nodes.find(n => n.id === edge.source)
    if (src && src.data.params) {
      return src.data.params.prompt_text || src.data.params.generated_prompt || node.data.params.prompt
    }
  }
  return node.data.params.prompt
}

async function generateImageHandler() {
  const node = store.selectedNode()
  if (!node || node.data.type !== 'ImageGenerationNode') return
  const prompt = resolveImagePrompt(node)
  if (!prompt || !prompt.trim()) {
    imgError.value = '请输入提示词，或连接提示词结果节点'
    return
  }
  generatingImage.value = true
  imgError.value = ''
  try {
    const resp = await generateImage({ prompt, model: node.data.params.model })
    if (resp.data.ok) {
      store.updateNodeParam(store.selectedNodeId, 'generated_images', resp.data.urls)
    } else {
      imgError.value = resp.data.error
    }
  } catch (e) {
    imgError.value = '生成失败: ' + e.message
  }
  generatingImage.value = false
}

async function copyPrompt() {
  const text = store.selectedNode()?.data.params.prompt_text
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch {}
}

onMounted(async () => {
  try {
    const resp = await getAiProviders()
    aiProviders.value = resp.data
  } catch {}
})

const currentProvider = computed(() => {
  const node = store.selectedNode()
  if (!node || node.data.type !== 'PromptGeneratorNode') return null
  return aiProviders.value.find(p => p.name === node.data.params.provider) || null
})

function handleWorkflowFile(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const json = JSON.parse(reader.result)
      store.updateNodeParam(store.selectedNodeId, 'workflow_json', json)
    } catch (err) {
      alert('JSON 解析失败: ' + err.message)
    }
  }
  reader.readAsText(file)
}

async function generatePromptHandler() {
  const node = store.selectedNode()
  if (!node || node.data.type !== 'PromptGeneratorNode') return
  const desc = node.data.params.description
  if (!desc || !desc.trim()) {
    genError.value = '请先输入角色描述'
    return
  }

  generating.value = true
  genError.value = ''
  store.updateNodeParam(store.selectedNodeId, 'generated_prompt', '')

  await generatePrompt(
    {
      provider: node.data.params.provider,
      model: node.data.params.model,
      description: desc,
      temperature: node.data.params.temperature ?? 0.8,
    },
    (fullText) => {
      store.updateNodeParam(store.selectedNodeId, 'generated_prompt', fullText)
      store.updatePromptResult(store.selectedNodeId, fullText)
    },
    (err) => {
      genError.value = err
    }
  )

  generating.value = false
}
</script>

<template>
  <div class="property-panel">
    <div v-if="!store.selectedNode()" class="empty-hint">点击节点进行编辑</div>

    <template v-else>
      <div class="panel-title">{{ store.selectedNode().data.label }}</div>

      <!-- 输入节点参数 -->
      <div v-if="store.selectedNode().data.type === 'InputNode'" class="params">
        <div class="param-row">
          <label>类型</label>
          <select
            :value="store.selectedNode().data.params.type"
            @change="store.updateNodeParam(store.selectedNodeId, 'type', $event.target.value)"
          >
            <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="param-row">
          <label>正向提示词</label>
          <textarea
            :value="store.selectedNode().data.params.prompt"
            rows="3"
            placeholder="输入正向提示词..."
            @input="store.updateNodeParam(store.selectedNodeId, 'prompt', $event.target.value)"
          />
        </div>
        <div class="param-row">
          <label>负向提示词</label>
          <textarea
            :value="store.selectedNode().data.params.negative_prompt"
            rows="2"
            placeholder="输入负向提示词..."
            @input="store.updateNodeParam(store.selectedNodeId, 'negative_prompt', $event.target.value)"
          />
        </div>
        <div class="param-row">
          <label>种子 (Seed)</label>
          <input
            type="number"
            :value="store.selectedNode().data.params.seed"
            @input="store.updateNodeParam(store.selectedNodeId, 'seed', $event.target.valueAsNumber || -1)"
          />
        </div>
        <div class="param-row half">
          <div>
            <label>宽度</label>
            <input
              type="number"
              :value="store.selectedNode().data.params.width"
              @input="store.updateNodeParam(store.selectedNodeId, 'width', $event.target.valueAsNumber || 512)"
            />
          </div>
          <div>
            <label>高度</label>
            <input
              type="number"
              :value="store.selectedNode().data.params.height"
              @input="store.updateNodeParam(store.selectedNodeId, 'height', $event.target.valueAsNumber || 512)"
            />
          </div>
        </div>
        <div class="param-row">
          <label>批次数量</label>
          <input
            type="number"
            :value="store.selectedNode().data.params.batch_size"
            @input="store.updateNodeParam(store.selectedNodeId, 'batch_size', $event.target.valueAsNumber || 1)"
          />
        </div>
      </div>

      <!-- 提示词生成节点参数 -->
      <div v-if="store.selectedNode().data.type === 'PromptGeneratorNode'" class="params">
        <div class="param-row">
          <label>角色描述</label>
          <textarea
            :value="store.selectedNode().data.params.description"
            rows="4"
            placeholder="例如：一个穿红色斗篷的年轻女法师，金色长发，蓝色眼睛..."
            @input="store.updateNodeParam(store.selectedNodeId, 'description', $event.target.value)"
          />
        </div>
        <div class="param-row">
          <label>提供商</label>
          <select
            :value="store.selectedNode().data.params.provider"
            @change="store.updateNodeParam(store.selectedNodeId, 'provider', $event.target.value); store.updateNodeParam(store.selectedNodeId, 'model', '')"
          >
            <option v-for="p in aiProviders" :key="p.name" :value="p.name">{{ p.name }}</option>
            <option v-if="aiProviders.length === 0" value="">（无提供商，请到工具栏 AI 设置）</option>
          </select>
        </div>
        <div class="param-row">
          <label>模型</label>
          <select
            :value="store.selectedNode().data.params.model"
            @change="store.updateNodeParam(store.selectedNodeId, 'model', $event.target.value)"
          >
            <option value="">（选择模型）</option>
            <option v-for="m in (currentProvider?.models || [])" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="param-row">
          <button class="btn-generate" :disabled="generating" @click="generatePromptHandler">
            {{ generating ? '生成中...' : '生成三视图提示词' }}
          </button>
          <div v-if="genError" class="gen-error">{{ genError }}</div>
        </div>
        <div class="param-row" v-if="store.selectedNode().data.params.generated_prompt || generating">
          <label>生成结果（三视图提示词）</label>
          <textarea
            :value="store.selectedNode().data.params.generated_prompt"
            rows="8"
            readonly
            class="preview"
            placeholder="点击生成后在此显示..."
          />
        </div>
        <button class="btn-delete" @click="store.removeNode(store.selectedNodeId)">删除节点</button>
      </div>

      <!-- 提示词结果节点 -->
      <div v-if="store.selectedNode().data.type === 'PromptResultNode'" class="params">
        <div class="param-row">
          <label>提示词内容</label>
          <textarea
            :value="store.selectedNode().data.params.prompt_text"
            rows="10"
            readonly
            class="preview"
            placeholder="由提示词生成节点自动填充..."
          />
        </div>
        <div class="param-row">
          <button class="btn-copy" @click="copyPrompt" :disabled="!store.selectedNode().data.params.prompt_text">
            {{ copied ? '已复制' : '复制提示词' }}
          </button>
        </div>
        <div class="hint" style="padding: 0 16px 8px;">将此节点的 PROMPT 输出连接到「输入」节点的 prompt 输入</div>
        <button class="btn-delete" @click="store.removeNode(store.selectedNodeId)">删除节点</button>
      </div>

      <!-- ComfyUI 节点参数 -->
      <div v-if="store.selectedNode().data.type === 'ComfyUINode'" class="params">
        <div class="param-row">
          <label>工作流配置</label>
          <input type="file" accept=".json" @change="handleWorkflowFile" class="file-input" />
          <div class="hint">上传 ComfyUI 工作流 JSON 文件，使用 {'{{'}参数名{'}}'} 作为占位符</div>
        </div>
        <div class="param-row">
          <label>工作流预览</label>
          <textarea
            :value="store.selectedNode().data.params.workflow_json ? JSON.stringify(store.selectedNode().data.params.workflow_json, null, 2) : ''"
            rows="12"
            readonly
            class="preview"
            placeholder="尚未加载工作流..."
          />
        </div>
        <button class="btn-delete" @click="store.removeNode(store.selectedNodeId)">删除节点</button>
      </div>

      <!-- 生图节点 -->
      <div v-if="store.selectedNode().data.type === 'ImageGenerationNode'" class="params">
        <div class="param-row">
          <label>提示词</label>
          <textarea
            :value="store.selectedNode().data.params.prompt"
            rows="4"
            placeholder="手动输入，或连接「提示词结果」节点自动获取"
            @input="store.updateNodeParam(store.selectedNodeId, 'prompt', $event.target.value)"
          />
        </div>
        <div class="param-row">
          <label>模型</label>
          <input
            type="text"
            :value="store.selectedNode().data.params.model"
            @input="store.updateNodeParam(store.selectedNodeId, 'model', $event.target.value)"
          />
        </div>
        <div class="param-row">
          <button class="btn-generate" :disabled="generatingImage" @click="generateImageHandler">
            {{ generatingImage ? '生成中...' : '生成图片' }}
          </button>
          <div v-if="imgError" class="gen-error">{{ imgError }}</div>
        </div>
        <div v-if="store.selectedNode().data.params.generated_images?.length" class="param-row">
          <label>生成结果</label>
          <img
            v-for="(img, i) in store.selectedNode().data.params.generated_images"
            :key="i"
            :src="img"
            class="gen-image"
          />
        </div>
        <button class="btn-delete" @click="store.removeNode(store.selectedNodeId)">删除节点</button>
      </div>

      <!-- 输出节点 -->
      <div v-if="store.selectedNode().data.type === 'OutputNode'" class="params">
        <div class="param-row">
          <div class="hint">连接 ComfyUI 节点的输出到此节点，执行后在此查看结果</div>
        </div>
        <button class="btn-delete" @click="store.removeNode(store.selectedNodeId)">删除节点</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.property-panel {
  width: 280px;
  min-width: 280px;
  background: #16213e;
  border-left: 1px solid #0f3460;
  overflow-y: auto;
}
.panel-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #0f3460;
}
.empty-hint {
  padding: 24px 16px;
  color: #666;
  font-size: 13px;
  text-align: center;
}
.params { padding: 8px 0; }
.param-row { padding: 6px 16px; }
.param-row label {
  display: block;
  font-size: 11px;
  color: #888;
  margin-bottom: 3px;
  text-transform: uppercase;
}
.param-row input, .param-row textarea, .param-row select {
  width: 100%;
  background: #0f3460;
  border: 1px solid #1a1a4e;
  color: #eee;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
}
.param-row input:focus, .param-row textarea:focus, .param-row select:focus {
  border-color: #e94560;
}
.param-row textarea { resize: vertical; }
.param-row textarea.preview {
  font-size: 10px;
  font-family: 'SF Mono', 'Menlo', monospace;
  opacity: 0.7;
}
.half { display: flex; gap: 8px; }
.half > div { flex: 1; }
.hint {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  line-height: 1.4;
}
.file-input {
  font-size: 12px;
  padding: 4px 0;
}
.btn-delete {
  margin: 12px 16px;
  padding: 6px 12px;
  background: #5a1a1a;
  border: 1px solid #8b3a3a;
  color: #e94560;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-delete:hover { background: #7a2a2a; }
.btn-copy {
  width: 100%;
  padding: 6px;
  background: #0f3460;
  border: 1px solid #1a1a4e;
  color: #66ccff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-copy:hover { background: #1a1a4e; }
.btn-copy:disabled { opacity: 0.4; cursor: not-allowed; }
.gen-image {
  width: 100%;
  border-radius: 6px;
  margin-top: 6px;
  display: block;
}
.btn-generate {
  width: 100%;
  padding: 8px;
  background: #4fc08d;
  border: 1px solid #3aa876;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
.btn-generate:hover { background: #3aa876; }
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }
.gen-error {
  font-size: 11px;
  color: #e94560;
  margin-top: 6px;
  line-height: 1.4;
}
</style>
