<script setup>
import { ref } from 'vue'
import { useWorkflowStore } from './stores/workflow.js'
import Toolbar from './components/Toolbar.vue'
import NodePanel from './components/NodePanel.vue'
import Canvas from './components/Canvas.vue'
import PropertyPanel from './components/PropertyPanel.vue'
import ProjectHome from './components/ProjectHome.vue'

const store = useWorkflowStore()
const showNodePanel = ref(true)
const showPropertyPanel = ref(true)
</script>

<template>
  <ProjectHome v-if="store.view === 'home'" />
  <div v-else class="app">
    <Toolbar v-model:show-node-panel="showNodePanel" v-model:show-property-panel="showPropertyPanel" />
    <div class="main">
      <NodePanel v-if="showNodePanel" />
      <Canvas />
      <PropertyPanel v-if="showPropertyPanel" />
    </div>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; overflow: hidden; }
.app { height: 100%; display: flex; flex-direction: column; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }
.main { flex: 1; display: flex; overflow: hidden; }
</style>
