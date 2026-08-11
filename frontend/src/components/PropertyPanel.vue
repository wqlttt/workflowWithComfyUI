<script setup>
import { useWorkflowStore } from '../stores/workflow.js'
import { NODE_DEFINITIONS } from '../utils/nodeDefinitions.js'

const store = useWorkflowStore()

const typeOptions = [
  { value: 'text2image', label: '文生图' },
  { value: 'text2video', label: '文生视频' },
  { value: 'img2img', label: '图生图' },
]

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
</style>
