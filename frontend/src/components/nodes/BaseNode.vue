<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  id: String,
  data: Object,
})

const inputCount = props.data.inputs ? props.data.inputs.length : 0
const outputCount = props.data.outputs ? props.data.outputs.length : 0

const colors = {
  InputNode: '#4fc08d',
  ComfyUINode: '#e94560',
  OutputNode: '#66ccff',
  PromptGeneratorNode: '#c792ea',
  PromptResultNode: '#f5a97f',
  ImageGenerationNode: '#f7d154',
}
const theme = computed(() => colors[props.data.type] || '#888')

// 结果节点展示流式文本
const resultPreview = computed(() => {
  if (props.data.type !== 'PromptResultNode') return ''
  return props.data.params?.prompt_text || ''
})
</script>

<template>
  <div class="base-node" :class="data.type" :style="{ borderColor: theme }">
    <template v-for="i in inputCount" :key="'in-' + i">
      <Handle
        :id="'input-' + (i - 1)"
        type="target"
        :position="Position.Left"
        :style="{ top: '24px', background: '#ffcc00', width: '9px', height: '9px', border: 'none' }"
      />
    </template>

    <template v-for="i in outputCount" :key="'out-' + i">
      <Handle
        :id="'output-' + (i - 1)"
        type="source"
        :position="Position.Right"
        :style="{ top: '24px', background: '#ffcc00', width: '9px', height: '9px', border: 'none' }"
      />
    </template>

    <div class="node-title" :style="{ background: theme }">
      <span class="title-dot" :style="{ background: theme }"></span>
      {{ data.label }}
    </div>

    <div class="node-body" v-if="data.params">
      <!-- 输入节点 -->
      <template v-if="data.type === 'InputNode'">
        <div class="preview-line">{{ data.params.prompt || '（空提示词）' }}</div>
      </template>

      <!-- 提示词生成节点 -->
      <template v-else-if="data.type === 'PromptGeneratorNode'">
        <div class="preview-line muted">
          {{ data.params.description || '（在右侧填写角色描述）' }}
        </div>
        <div class="status-badge" :class="data.params.generated_prompt ? 'done' : 'idle'">
          {{ data.params.generated_prompt ? '已生成' : '待生成' }}
        </div>
      </template>

      <!-- 提示词结果节点 -->
      <template v-else-if="data.type === 'PromptResultNode'">
        <div v-if="resultPreview" class="result-text nowheel">{{ resultPreview }}</div>
        <div v-else class="result-empty">
          <span class="pulse-dot"></span> 等待生成...
        </div>
      </template>

      <!-- 生图节点 -->
      <template v-else-if="data.type === 'ImageGenerationNode'">
        <div class="preview-line muted">{{ data.params.prompt || '（连接提示词结果或填写提示词）' }}</div>
        <div v-if="data.params.generated_images?.length" class="node-thumb">
          <img :src="data.params.generated_images[0]" alt="generated" />
        </div>
      </template>

      <!-- ComfyUI 节点 -->
      <template v-else-if="data.type === 'ComfyUINode'">
        <div class="preview-line">
          {{ data.params.workflow_json && typeof data.params.workflow_json === 'object' ? '工作流已配置' : '未配置工作流' }}
        </div>
      </template>

      <!-- 输出节点 -->
      <template v-else-if="data.type === 'OutputNode'">
        <div class="preview-line muted">接收生成结果</div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.base-node {
  border: 2px solid;
  border-radius: 10px;
  min-width: 180px;
  background: #1a1a3e;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  position: relative;
  overflow: hidden;
}
.base-node.PromptResultNode { min-width: 240px; max-width: 300px; }

.node-title {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 6px currentColor;
}

.node-body { padding: 8px 12px 10px; }

.preview-line {
  font-size: 11px;
  color: #ccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}
.preview-line.muted { color: #888; }

.node-thumb {
  margin-top: 6px;
  border-radius: 6px;
  overflow: hidden;
}
.node-thumb img {
  width: 100%;
  display: block;
}

.status-badge {
  margin-top: 6px;
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
}
.status-badge.done { background: rgba(79, 192, 141, 0.2); color: #4fc08d; }
.status-badge.idle { background: rgba(136, 136, 136, 0.15); color: #888; }

.result-text {
  font-size: 11px;
  color: #eee;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}
.result-text::-webkit-scrollbar { width: 4px; }
.result-text::-webkit-scrollbar-thumb { background: #555; border-radius: 2px; }
.result-text::-webkit-scrollbar-track { background: transparent; }

.result-empty {
  font-size: 11px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 6px;
}
.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f5a97f;
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.1); }
}
</style>
