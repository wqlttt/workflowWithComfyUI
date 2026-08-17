<script setup>
import { markRaw } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import { useWorkflowStore } from '../stores/workflow.js'
import { NODE_DEFINITIONS } from '../utils/nodeDefinitions.js'
import BaseNode from './nodes/BaseNode.vue'

const store = useWorkflowStore()

const nodeTypes = {
  custom: markRaw(BaseNode),
}

const { onConnect, addEdges, onNodeClick, screenToFlowCoordinate } = useVueFlow()

onConnect((connection) => {
  addEdges([connection])
})

onNodeClick(({ node }) => {
  store.selectedNodeId = node.id
})

function onDrop(event) {
  const nodeType = event.dataTransfer.getData('nodeType')
  if (!nodeType || !NODE_DEFINITIONS[nodeType]) return

  const position = screenToFlowCoordinate({
    x: event.clientX,
    y: event.clientY,
  })

  store.addNode(nodeType, position)
}
</script>

<template>
  <div class="canvas-wrapper" @drop="onDrop" @dragover.prevent @dragenter.prevent>
    <VueFlow
      v-model:nodes="store.nodes"
      v-model:edges="store.edges"
      :node-types="nodeTypes"
      :default-edge-options="{ animated: true, style: { stroke: '#66ccff', strokeWidth: 2 } }"
      no-wheel-class-name="nowheel"
      fit-view-on-init
      @pane-click="store.selectedNodeId = null"
    >
      <Background :gap="20" />
      <Controls />
      <MiniMap />
    </VueFlow>
  </div>
</template>

<style scoped>
.canvas-wrapper {
  flex: 1;
  height: 100%;
}
</style>
