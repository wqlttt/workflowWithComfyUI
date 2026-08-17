<script setup>
import { NODE_DEFINITIONS } from '../utils/nodeDefinitions.js'

const categories = ['input', 'core', 'output']
const categoryLabels = { input: '输入', core: '核心', output: '输出' }
const categoryColors = { input: '#4fc08d', core: '#e94560', output: '#66ccff' }

function onDragStart(event, nodeType) {
  event.dataTransfer.setData('nodeType', nodeType)
  event.dataTransfer.effectAllowed = 'move'
}
</script>

<template>
  <div class="node-panel">
    <div class="panel-title">节点列表</div>
    <div v-for="cat in categories" :key="cat" class="category">
      <div class="cat-title">{{ categoryLabels[cat] }}</div>
      <div
        v-for="(def, type) in NODE_DEFINITIONS"
        :key="type"
      >
        <div
          v-if="def.category === cat && type !== 'PromptResultNode'"
          class="node-item"
          draggable="true"
          @dragstart="onDragStart($event, type)"
          :style="{ borderLeftColor: categoryColors[cat] }"
        >
          {{ def.label }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.node-panel {
  width: 180px;
  min-width: 180px;
  background: #16213e;
  border-right: 1px solid #0f3460;
  overflow-y: auto;
}
.panel-title {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid #0f3460;
  color: #e94560;
}
.category { padding: 8px 0; }
.cat-title {
  padding: 4px 16px;
  font-size: 11px;
  text-transform: uppercase;
  color: #888;
  letter-spacing: 1px;
}
.node-item {
  padding: 6px 16px 6px 22px;
  font-size: 13px;
  cursor: grab;
  transition: background .15s;
  color: #ccc;
  border-left: 3px solid transparent;
}
.node-item:hover { background: #0f3460; color: #fff; }
.node-item:active { cursor: grabbing; }
</style>
