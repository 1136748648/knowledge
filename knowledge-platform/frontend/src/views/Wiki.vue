<template>
  <div class="wiki-page fade-in">
    <div class="page-header">
      <div>
        <h1>{{ t('wiki.title') }}</h1>
        <p>{{ t('wiki.subtitle') }}</p>
      </div>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon>{{ t('common.action.createDoc') }}
      </el-button>
    </div>

    <div class="wiki-layout">
      <!-- 左侧目录树 -->
      <div class="wiki-sidebar">
        <el-input v-model="searchQuery" :placeholder="t('wiki.searchPlaceholder')" prefix-icon="Search" clearable class="search-input" />
        <el-tree
          :data="treeData"
          :props="{ label: 'title', children: 'children' }"
          highlight-current
          default-expand-all
          @node-click="selectNode"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <el-icon><Document /></el-icon>
              <span>{{ node.label }}</span>
            </div>
          </template>
        </el-tree>
      </div>

      <!-- 右侧内容区 -->
      <div class="wiki-content" v-loading="loadingPage" :element-loading-text="t('common.status.loading')">
        <div v-if="!selectedPage" class="empty-state">
          <el-icon :size="64" color="#E5E7EB"><Document /></el-icon>
          <h3>{{ t('wiki.selectHint') }}</h3>
        </div>
        <div v-else>
          <div class="content-header">
            <h2>{{ selectedPage.title }}</h2>
            <div class="content-meta">
              <el-tag :type="sensitivityType(selectedPage.sensitivity)" size="small">
                {{ selectedPage.sensitivity }}
              </el-tag>
              <span>{{ selectedPage.created_by }} · {{ selectedPage.created_at }}</span>
            </div>
          </div>
          <div class="content-body" v-html="renderMarkdown(selectedPage.content)" />
        </div>
      </div>
    </div>

    <!-- 创建对话框 -->
    <el-dialog v-model="showCreate" :title="t('wiki.create.title')" width="600px" :close-on-click-modal="!creating">
      <el-form label-position="top" v-loading="creating" :element-loading-text="t('common.status.creating')">
        <el-form-item :label="t('wiki.create.titleLabel')" required>
          <el-input v-model="newPage.title" :placeholder="t('wiki.create.titlePlaceholder')" :disabled="creating" />
        </el-form-item>
        <el-form-item :label="t('wiki.create.slugLabel')" required>
          <el-input v-model="newPage.slug" :placeholder="t('wiki.create.slugPlaceholder')" :disabled="creating" />
        </el-form-item>
        <el-form-item :label="t('wiki.create.sensitivityLabel')">
          <el-select v-model="newPage.sensitivity" :disabled="creating">
            <el-option :label="t('wiki.sensitivity.public')" value="public" />
            <el-option :label="t('wiki.sensitivity.internal')" value="internal" />
            <el-option :label="t('wiki.sensitivity.confidential')" value="confidential" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('wiki.create.contentLabel')" required>
          <el-input v-model="newPage.content" type="textarea" :rows="10" :placeholder="t('wiki.create.contentPlaceholder')" :disabled="creating" />
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
import { ElMessage } from 'element-plus'
import { getWikiPages, getWikiPage, createWikiPage } from '@/api/wiki'

const { t } = useI18n()

const searchQuery = ref('')
const treeData = ref([])
const selectedPage = ref(null)
const showCreate = ref(false)
const creating = ref(false)
const loadingPage = ref(false)

const newPage = reactive({
  title: '',
  slug: '',
  content: '',
  sensitivity: 'public',
})

onMounted(async () => {
  await loadPages()
})

async function loadPages() {
  try {
    const pages = await getWikiPages()
    treeData.value = buildTree(pages)
  } catch (e) {
    // ignore
  }
}

function buildTree(pages) {
  const map = {}
  const roots = []
  pages.forEach(p => { map[p.id] = { ...p, children: [] } })
  pages.forEach(p => {
    if (p.parent_id && map[p.parent_id]) {
      map[p.parent_id].children.push(map[p.id])
    } else {
      roots.push(map[p.id])
    }
  })
  return roots
}

async function selectNode(data) {
  loadingPage.value = true
  try {
    selectedPage.value = await getWikiPage(data.id)
  } catch (e) {
    ElMessage.error(t('wiki.loadFailed'))
  } finally { loadingPage.value = false }
}

async function handleCreate() {
  if (!newPage.title || !newPage.slug || !newPage.content) {
    ElMessage.warning(t('wiki.create.required'))
    return
  }
  creating.value = true
  try {
    await createWikiPage(newPage)
    ElMessage.success(t('wiki.create.success'))
    showCreate.value = false
    await loadPages()
  } catch (e) {
    ElMessage.error(t('common.msg.createFailed'))
  } finally { creating.value = false }
}

function sensitivityType(s) {
  const map = { public: 'success', internal: 'warning', confidential: 'danger', secret: 'danger' }
  return map[s] || 'info'
}

function renderMarkdown(text) {
  // 简单的 Markdown 渲染（后续可用 markdown-it）
  return text?.replace(/\n/g, '<br>') || ''
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

.wiki-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 200px);
}

.wiki-sidebar {
  width: 280px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
  overflow-y: auto;
}

.search-input {
  margin-bottom: 16px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
}

.wiki-content {
  flex: 1;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 24px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-state h3 { margin-top: 16px; color: var(--color-text); }

.content-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.content-header h2 { font-size: var(--font-size-xl); }

.content-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.content-body {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--color-text-secondary);
}
</style>
