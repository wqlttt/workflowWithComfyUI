<script setup>
import { ref, onMounted } from 'vue'
import { useWorkflowStore } from '../stores/workflow.js'

const store = useWorkflowStore()
const showCreateDialog = ref(false)
const newName = ref('')

onMounted(() => {
  store.fetchProjects()
})

function formatTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return iso
  }
}

async function handleCreate() {
  const name = newName.value.trim() || '未命名项目'
  await store.createProject(name)
  showCreateDialog.value = false
  newName.value = ''
}

async function handleDelete(id, e) {
  e.stopPropagation()
  if (!confirm('确定删除这个项目？')) return
  await store.removeProject(id)
}
</script>

<template>
  <div class="home">
    <div class="home-header">
      <div class="home-title">我的工作流</div>
      <button class="btn-new" @click="showCreateDialog = true">＋ 新建项目</button>
    </div>

    <div class="project-grid">
      <div
        v-for="p in store.projects"
        :key="p.id"
        class="project-card"
        @click="store.openProject(p.id)"
      >
        <div class="card-top">
          <span class="card-name">{{ p.name }}</span>
          <button class="card-del" @click="handleDelete(p.id, $event)" title="删除">✕</button>
        </div>
        <div class="card-meta">
          <span>{{ p.node_count }} 个节点</span>
          <span v-if="p.image_count"> · {{ p.image_count }} 张图</span>
        </div>
        <div class="card-time">{{ formatTime(p.updated_at) }}</div>
      </div>

      <div v-if="store.projects.length === 0" class="empty-state">
        <div class="empty-icon">🗂️</div>
        <div>还没有项目</div>
        <div class="empty-hint">点击右上角「新建项目」开始</div>
      </div>
    </div>

    <!-- 新建项目弹窗 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click.self="showCreateDialog = false">
      <div class="modal">
        <h3>新建项目</h3>
        <label>项目名称</label>
        <input v-model="newName" placeholder="输入项目名称" @keyup.enter="handleCreate" />
        <div class="modal-actions">
          <button @click="handleCreate">创建</button>
          <button @click="showCreateDialog = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home {
  height: 100%;
  background: #1a1a2e;
  color: #eee;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 40px;
  border-bottom: 1px solid #0f3460;
}
.home-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.btn-new {
  background: #e94560;
  border: none;
  color: #fff;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}
.btn-new:hover { background: #c73a52; }

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  padding: 32px 40px;
}
.project-card {
  background: #16213e;
  border: 1px solid #0f3460;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all .15s;
}
.project-card:hover {
  border-color: #e94560;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,.4);
}
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-del {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
}
.card-del:hover { color: #e94560; background: rgba(233,69,96,.15); }
.card-meta { font-size: 12px; color: #888; margin-bottom: 4px; }
.card-time { font-size: 11px; color: #555; }

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 0;
  color: #666;
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-hint { font-size: 13px; margin-top: 8px; }

.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: #16213e; border: 1px solid #0f3460; border-radius: 8px;
  padding: 20px; min-width: 320px;
}
.modal h3 { margin-bottom: 12px; font-size: 15px; color: #fff; }
.modal label { font-size: 12px; color: #888; display: block; margin-bottom: 4px; }
.modal input { width: 100%; background: #0f3460; border: 1px solid #1a1a4e; color: #eee; padding: 8px; border-radius: 4px; outline: none; font-size: 13px; }
.modal-actions { margin-top: 14px; display: flex; gap: 8px; justify-content: flex-end; }
.modal-actions button { padding: 6px 16px; border-radius: 4px; border: 1px solid #0f3460; background: #0f3460; color: #eee; cursor: pointer; font-size: 12px; }
.modal-actions button:first-child { background: #e94560; border-color: #e94560; }
.modal-actions button:hover { opacity: 0.9; }
</style>
