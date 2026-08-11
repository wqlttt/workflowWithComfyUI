<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  id: String,
  data: Object,
})

const inputCount = props.data.inputs ? props.data.inputs.length : 0
const outputCount = props.data.outputs ? props.data.outputs.length : 0

const colors = { InputNode: '#4fc08d', ComfyUINode: '#e94560', OutputNode: '#66ccff' }
const theme = computed(() => colors[props.data.type] || '#888')
</script>

<template>
  <div class="base-node" :style="{ borderColor: theme, background: theme + '15' }">
    <template v-for="i in inputCount" :key="'in-' + i">
      <Handle
        :id="'input-' + (i - 1)"
        type="target"
        :position="Position.Left"
        :style="{ top: (24 + (i - 1) * 20) + 'px', background: '#ffcc00', width: '8px', height: '8px', border: 'none' }"
      />
    </template>

    <template v-for="i in outputCount" :key="'out-' + i">
      <Handle
        :id="'output-' + (i - 1)"
        type="source"
        :position="Position.Right"
        :style="{ top: (24 + (i - 1) * 20) + 'px', background: '#ffcc00', width: '8px', height: '8px', border: 'none' }"
      />
    </template>

    <div class="node-title" :style="{ background: theme, color: '#fff' }">{{ data.label }}</div>
    <div class="node-params-preview" v-if="data.params">
      <template v-if="data.type === 'InputNode'">
        <div class="param-preview">
          <span class="val">{{ data.params.prompt || '(空提示词)' }}</span>
        </div>
      </template>
      <template v-else-if="data.type === 'ComfyUINode'">
        <div class="param-preview">
          <span class="val">{{ data.params.workflow_json && typeof data.params.workflow_json === 'object' ? '已配置' : '未配置' }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.base-node {
  border: 2px solid;
  border-radius: 8px;
  min-width: 160px;
  position: relative;
}
.node-title {
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px 6px 0 0;
  text-align: center;
}
.node-params-preview {
  padding: 6px 10px 8px;
}
.param-preview {
  font-size: 11px;
  padding: 1px 0;
}
.param-preview .val {
  color: #bbb;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}
</style>
