<template>
  <div class="wiki-page fade-in">
    <!-- 创建/编辑全屏页面 -->
    <div v-if="editorMode" class="editor-page">
      <div class="editor-header">
        <div class="editor-title-row">
          <el-input v-model="editorForm.title" :placeholder="t('wiki.create.titlePlaceholder')" class="title-input" size="large" :disabled="saving" />
          <el-input v-model="editorForm.slug" :placeholder="t('wiki.create.slugPlaceholder')" class="slug-input" size="large" :disabled="saving" />
          <el-select v-model="editorForm.sensitivity" class="sensitivity-select" size="large" :disabled="saving">
            <el-option :label="t('wiki.sensitivity.public')" value="public" />
            <el-option :label="t('wiki.sensitivity.internal')" value="internal" />
            <el-option :label="t('wiki.sensitivity.confidential')" value="confidential" />
          </el-select>
        </div>
        <div class="editor-actions">
          <el-button @click="closeEditor" :disabled="saving">{{ t('common.btn.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">{{ editorMode === 'create' ? t('common.action.create') : t('common.btn.save') }}</el-button>
        </div>
      </div>
      <div class="editor-body">
        <div class="editor-left">
          <div class="editor-label">{{ t('wiki.create.contentLabel') }}</div>
          <textarea v-model="editorForm.content" :placeholder="t('wiki.create.contentPlaceholder')" :disabled="saving" class="md-editor" />
          <div class="upload-section" style="margin-top: 16px;">
            <div class="editor-label">{{ t('wiki.uploadFile') }}</div>
            <el-upload
              class="upload-demo"
              action="#"
              :http-request="handleUpload"
              :before-upload="beforeUpload"
              :disabled="saving || uploadProgress > 0"
              accept=".md,.txt,.pdf,.doc,.docx"
            >
              <el-button size="small" :loading="uploadProgress > 0">
                <el-icon><Upload /></el-icon>
                {{ uploadProgress > 0 ? `${uploadProgress}%` : t('wiki.uploadBtn') }}
              </el-button>
            </el-upload>
            <div v-if="uploadedFile" class="uploaded-file">
              <el-icon><FileText /></el-icon>
              <span>{{ uploadedFile.name }}</span>
              <el-button text size="small" @click="clearUpload">×</el-button>
            </div>
          </div>
        </div>
        <div class="editor-right">
          <div class="editor-label">{{ t('wiki.create.preview') }}</div>
          <div class="markdown-body preview-area" v-html="previewHtml" />
        </div>
      </div>
    </div>

    <!-- 主页面 -->
    <template v-else>
      <div class="page-header">
        <div>
          <h1>{{ t('wiki.title') }}</h1>
          <p>{{ t('wiki.subtitle') }}</p>
        </div>
        <el-button type="primary" @click="openCreate">
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
              <div class="content-actions">
                <el-button text type="primary" @click="openEdit">{{ t('common.action.edit') }}</el-button>
                <el-button text type="danger" :loading="deleting" @click="handleDelete">{{ t('common.btn.delete') }}</el-button>
              </div>
            </div>
            
            <div v-if="processStatus === 'processing'" class="process-status processing">
              <el-spinner size="24" />
              <span>{{ t('wiki.processing') }}</span>
            </div>
            
            <div v-if="processStatus === 'completed'" class="process-status completed">
              <el-icon :size="24" color="#22c55e"><CheckCircle /></el-icon>
              <span>{{ t('wiki.processCompleted') }}</span>
            </div>
            
            <div v-if="processStatus === 'failed'" class="process-status failed">
              <el-icon :size="24" color="#ef4444"><AlertCircle /></el-icon>
              <span>{{ t('wiki.processFailed') }}</span>
              <span class="error-message">{{ processError }}</span>
              <el-button size="small" @click="retryProcess">
                <el-icon><RefreshCw /></el-icon>
                {{ t('common.btn.retry') }}
              </el-button>
            </div>
            
            <div class="markdown-body" v-html="renderedContent" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Upload, FileText, RefreshCw } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { getWikiPages, getWikiPage, createWikiPage, updateWikiPage, deleteWikiPage, getUploadUrl, uploadFile, processDocument, getProcessStatus } from '@/api/wiki'

const { t } = useI18n()

const searchQuery = ref('')
const treeData = ref([])
const selectedPage = ref(null)
const editorMode = ref(null) // null | 'create' | 'edit'
const saving = ref(false)
const deleting = ref(false)
const loadingPage = ref(false)

const editorForm = reactive({
  id: null,
  title: '',
  slug: '',
  content: '',
  sensitivity: 'public',
})

const uploadProgress = ref(0)
const uploadedFile = ref(null)
const processStatus = ref(null)
const processError = ref(null)
let pollInterval = null

const previewHtml = computed(() => marked(editorForm.content || ''))
const renderedContent = computed(() => marked(selectedPage.value?.content || ''))

onMounted(async () => {
  await loadPages()
})

function openCreate() {
  editorMode.value = 'create'
  editorForm.id = null
  editorForm.title = ''
  editorForm.slug = ''
  editorForm.content = ''
  editorForm.sensitivity = 'public'
}

function openEdit() {
  if (!selectedPage.value) return
  editorMode.value = 'edit'
  editorForm.id = selectedPage.value.id
  editorForm.title = selectedPage.value.title || ''
  editorForm.slug = selectedPage.value.slug || ''
  editorForm.content = selectedPage.value.content || ''
  editorForm.sensitivity = selectedPage.value.sensitivity || 'public'
}

function closeEditor() {
  editorMode.value = null
}

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

async function beforeUpload(file) {
  const allowedTypes = ['.md', '.txt', '.pdf', '.doc', '.docx']
  const ext = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (!allowedTypes.includes(ext)) {
    ElMessage.warning(t('wiki.uploadInvalid'))
    return false
  }
  return true
}

async function handleUpload(params) {
  const file = params.file
  uploadProgress.value = 0
  try {
    const { url } = await getUploadUrl(file.name)
    const response = await fetch(url, {
      method: 'PUT',
      body: file,
    })
    if (response.ok) {
      uploadProgress.value = 100
      uploadedFile.value = file
      ElMessage.success(t('wiki.uploadSuccess'))
    } else {
      ElMessage.error(t('wiki.uploadFailed'))
    }
  } catch {
    ElMessage.error(t('wiki.uploadFailed'))
  } finally {
    uploadProgress.value = 0
  }
}

function clearUpload() {
  uploadedFile.value = null
}

async function handleSave() {
  if (!editorForm.title || !editorForm.slug) {
    ElMessage.warning(t('wiki.create.required'))
    return
  }
  saving.value = true
  try {
    let pageId = editorForm.id
    if (editorMode.value === 'create') {
      const result = await createWikiPage(editorForm)
      pageId = result.id
      ElMessage.success(t('wiki.create.success'))
    } else {
      await updateWikiPage(editorForm.id, editorForm)
      ElMessage.success(t('wiki.edit.success'))
    }
    
    if (uploadedFile.value) {
      await processDocument(pageId, uploadedFile.value.name)
      startPolling(pageId)
      uploadedFile.value = null
    }
    
    editorMode.value = null
    await loadPages()
    if (pageId) {
      selectedPage.value = await getWikiPage(pageId)
    }
  } catch (e) {
    ElMessage.error(editorMode.value === 'create' ? t('common.msg.createFailed') : t('common.msg.saveFailed'))
  } finally { saving.value = false }
}

function startPolling(pageId) {
  processStatus.value = 'processing'
  processError.value = null
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(async () => {
    try {
      const status = await getProcessStatus(pageId)
      processStatus.value = status.status
      if (status.status === 'completed') {
        stopPolling()
        ElMessage.success(t('wiki.processSuccess'))
      } else if (status.status === 'failed') {
        stopPolling()
        processError.value = status.error
      }
    } catch {
      stopPolling()
    }
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onUnmounted(() => {
  stopPolling()
})

async function retryProcess() {
  if (selectedPage.value) {
    await processDocument(selectedPage.value.id, '')
    startPolling(selectedPage.value.id)
  }
}

async function handleDelete() {
  if (!selectedPage.value) return
  await ElMessageBox.confirm(t('wiki.delete.confirm'), t('common.msg.confirmDelete'), { type: 'warning' })
  deleting.value = true
  try {
    await deleteWikiPage(selectedPage.value.id)
    ElMessage.success(t('common.msg.deleteSuccess'))
    selectedPage.value = null
    await loadPages()
  } catch (e) {
    ElMessage.error(t('common.msg.deleteFailed'))
  } finally { deleting.value = false }
}

function sensitivityType(s) {
  const map = { public: 'success', internal: 'warning', confidential: 'danger', secret: 'danger' }
  return map[s] || 'info'
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

.search-input { margin-bottom: 16px; }

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
.content-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

/* ---- Editor full page ---- */
.editor-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.editor-title-row {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.title-input { flex: 2; min-width: 200px; }
.slug-input { flex: 1; min-width: 140px; }
.sensitivity-select { width: 140px; }

.editor-actions {
  display: flex;
  gap: 8px;
}

.editor-body {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.editor-left, .editor-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
  overflow: hidden;
}

.editor-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.md-editor {
  flex: 1;
  width: 100%;
  resize: none;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 14px;
  line-height: 1.6;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: 12px;
  outline: none;
  background: transparent;
  color: var(--color-text);
}

.md-editor:focus {
  border-color: var(--color-primary);
}

.editor-right {
  overflow-y: auto;
}

.preview-area {
  flex: 1;
  overflow-y: auto;
}

/* ---- Markdown body ---- */
.markdown-body {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--color-text);
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  font-weight: 600;
}
.markdown-body :deep(h1) { font-size: 1.6em; border-bottom: 1px solid var(--color-border-light); padding-bottom: 8px; }
.markdown-body :deep(h2) { font-size: 1.4em; }
.markdown-body :deep(h3) { font-size: 1.2em; }

.markdown-body :deep(p) { margin: 8px 0; }

.markdown-body :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--color-primary);
  padding-left: 16px;
  color: var(--color-text-secondary);
  margin: 12px 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--color-border-light);
  padding: 8px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f9fafb;
  font-weight: 600;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border-light);
  margin: 24px 0;
}

.upload-section {
  padding: 12px;
  border: 1px dashed var(--color-border-light);
  border-radius: var(--radius-md);
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: var(--radius-sm);
}

.process-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border-radius: var(--radius-md);
}

.process-status.processing {
  background: #fef3c7;
  color: #d97706;
}

.process-status.completed {
  background: #dcfce7;
  color: #16a34a;
}

.process-status.failed {
  background: #fee2e2;
  color: #dc2626;
}

.process-status .error-message {
  font-size: var(--font-size-sm);
  margin-left: auto;
  margin-right: 12px;
}
</style>
