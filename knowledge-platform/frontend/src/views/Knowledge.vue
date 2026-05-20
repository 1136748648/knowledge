<template>
  <div class="knowledge-page fade-in">
    <div class="page-header">
      <div>
        <h1>{{ t('knowledge.title') }}</h1>
        <p>{{ t('knowledge.subtitle') }}</p>
      </div>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon>{{ t('common.action.createNode') }}
      </el-button>
    </div>

    <el-row :gutter="20">
      <!-- 左侧导航树 -->
      <el-col :xs="24" :md="8">
        <div class="nav-tree-card" v-loading="deleting" :element-loading-text="t('common.status.deleting')">
          <el-tree
            :data="navTree"
            :props="{ label: 'name', children: 'children' }"
            highlight-current
            default-expand-all
            @node-click="selectNode"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <el-icon><Folder /></el-icon>
                <span>{{ node.label }}</span>
                <el-tag v-if="data.visibility_roles?.length" size="small" type="warning">
                  {{ t('knowledge.restricted') }}
                </el-tag>
              </div>
            </template>
          </el-tree>
        </div>
      </el-col>

      <!-- 右侧详情 -->
      <el-col :xs="24" :md="16">
        <div v-if="!selectedNode" class="empty-state">
          <el-icon :size="64" color="#E5E7EB"><Compass /></el-icon>
          <h3>{{ t('knowledge.selectHint') }}</h3>
        </div>
        <div v-else class="node-detail">
          <div class="detail-header">
            <h2>{{ selectedNode.name }}</h2>
            <div class="detail-actions">
              <el-button text type="primary" @click="editNode" :disabled="deleting">{{ t('common.action.edit') }}</el-button>
              <el-button text type="danger" :loading="deleting" @click="deleteNode">{{ t('common.btn.delete') }}</el-button>
            </div>
          </div>
          <div class="detail-info">
            <div class="info-item">
              <span class="info-label">{{ t('knowledge.path') }}：</span>
              <span>{{ selectedNode.path }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('knowledge.visibleRoles') }}：</span>
              <el-tag v-for="r in (selectedNode.visibility_roles || [])" :key="r" size="small">{{ r }}</el-tag>
              <span v-if="!selectedNode.visibility_roles?.length">{{ t('knowledge.allVisible') }}</span>
            </div>
            <div v-if="selectedNode.description" class="info-item">
              <span class="info-label">{{ t('knowledge.description') }}：</span>
              <span>{{ selectedNode.description }}</span>
            </div>
          </div>

          <el-divider />

          <h3>{{ t('knowledge.linkedContent') }}</h3>
          <div class="linked-content">
            <el-empty v-if="!linkedItems.length" :description="t('knowledge.noLinkedContent')" />
            <div v-for="item in linkedItems" :key="item.id" class="linked-item">
              <el-icon><Document /></el-icon>
              <span>{{ item.content_type }} · {{ item.content_id }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 创建对话框 -->
    <el-dialog v-model="showCreate" :title="t('knowledge.create.title')" width="500px" :close-on-click-modal="!creating">
      <el-form label-position="top" v-loading="creating" :element-loading-text="t('common.status.creating')">
        <el-form-item :label="t('knowledge.create.nameLabel')" required>
          <el-input v-model="newNode.name" :placeholder="t('knowledge.create.namePlaceholder')" :disabled="creating" />
        </el-form-item>
        <el-form-item :label="t('knowledge.create.iconLabel')">
          <el-input v-model="newNode.icon" :placeholder="t('knowledge.create.iconPlaceholder')" :disabled="creating" />
        </el-form-item>
        <el-form-item :label="t('knowledge.create.descLabel')">
          <el-input v-model="newNode.description" type="textarea" :rows="3" :disabled="creating" />
        </el-form-item>
        <el-form-item :label="t('knowledge.create.rolesLabel')">
          <el-select v-model="newNode.visibility_roles" multiple :placeholder="t('knowledge.create.rolesPlaceholder')" :disabled="creating">
            <el-option :label="t('knowledge.create.roleAdmin')" value="admin" />
            <el-option :label="t('knowledge.create.roleHR')" value="hr" />
            <el-option :label="t('knowledge.create.roleManager')" value="manager" />
            <el-option :label="t('knowledge.create.roleEmployee')" value="employee" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false" :disabled="creating">{{ t('common.btn.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">{{ t('common.action.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getNavTree, createNavNode, deleteNavNode } from '@/api/knowledge'

const { t } = useI18n()

const navTree = ref([])
const selectedNode = ref(null)
const linkedItems = ref([])
const showCreate = ref(false)
const creating = ref(false)
const deleting = ref(false)

const newNode = reactive({
  name: '',
  icon: '',
  description: '',
  visibility_roles: [],
  parent_id: null,
})

onMounted(async () => {
  await loadTree()
})

async function loadTree() {
  try {
    navTree.value = await getNavTree()
  } catch (e) {
    // ignore
  }
}

function selectNode(data) {
  selectedNode.value = data
}

function editNode() {
  ElMessage.info(t('common.status.loading'))
}

async function deleteNode() {
  await ElMessageBox.confirm(t('common.msg.confirmDelete'), t('common.msg.confirmDelete'), { type: 'warning' })
  deleting.value = true
  try {
    await deleteNavNode(selectedNode.value.id)
    ElMessage.success(t('common.msg.deleteSuccess'))
    selectedNode.value = null
    await loadTree()
  } catch (e) {
    ElMessage.error(t('common.msg.deleteFailed'))
  } finally { deleting.value = false }
}

async function handleCreate() {
  if (!newNode.name) {
    ElMessage.warning(t('knowledge.create.nameRequired'))
    return
  }
  creating.value = true
  try {
    await createNavNode(newNode)
    ElMessage.success(t('common.msg.createSuccess'))
    showCreate.value = false
    await loadTree()
  } catch (e) {
    ElMessage.error(t('common.msg.createFailed'))
  } finally { creating.value = false }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-header h1 { font-size: var(--font-size-2xl); }
.page-header p { color: var(--color-text-secondary); font-size: var(--font-size-sm); }

.nav-tree-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
  min-height: 400px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
}

.empty-state {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.empty-state h3 { margin-top: 16px; color: var(--color-text); }

.node-detail {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 24px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h2 { font-size: var(--font-size-xl); }

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: var(--font-size-sm);
}

.info-label {
  color: var(--color-text-secondary);
  min-width: 80px;
}

.linked-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.linked-item:hover {
  background: var(--color-primary-50);
}
</style>
