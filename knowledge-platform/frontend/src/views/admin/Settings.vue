<template>
  <div class="settings-page fade-in">
    <div class="page-header">
      <h1>{{ t('settings.title') }}</h1>
      <p>{{ t('settings.subtitle') }}</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- AI 模型 -->
      <el-tab-pane :label="t('settings.tabs.llm')" name="llm">
        <div class="tab-content" v-loading="saving === 'llm' || testing === 'llm'" :element-loading-text="t('common.status.processing')">
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.llm.provider')">
              <el-select v-model="llmForm.provider" filterable allow-create :placeholder="t('settings.llm.providerPlaceholder')" @change="onProviderChange" :disabled="!!saving || !!testing">
                <el-option v-for="p in providers" :key="p.name" :label="p.display_name" :value="p.name">
                  <div class="provider-option">
                    <span>{{ p.display_name }}</span>
                    <el-tag v-if="p.supports_embedding" size="small" type="success">{{ t('settings.llm.supportsEmbedding') }}</el-tag>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item :label="t('settings.llm.apiKey')">
              <el-input v-model="llmForm.api_key" :placeholder="t('settings.llm.apiKeyPlaceholder')" show-password :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.llm.apiBase')">
              <el-input v-model="llmForm.api_base" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.llm.chatModel')">
              <div class="model-input-row">
                <el-select v-model="llmForm.model" filterable allow-create :placeholder="t('settings.llm.modelPlaceholder')" class="model-select" :disabled="!!saving || !!testing || fetchingModels">
                  <el-option v-for="m in chatModels" :key="m.id" :label="m.name" :value="m.id" />
                </el-select>
                <el-button type="primary" plain :loading="fetchingModels" @click="fetchRemoteModels" :disabled="!llmForm.api_key || !llmForm.api_base || !!saving || !!testing">
                  {{ t('common.btn.fetchModels') }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item :label="t('settings.llm.embeddingModel')">
              <div class="model-input-row">
                <el-select v-model="llmForm.embedding_model" filterable allow-create :placeholder="t('settings.llm.modelPlaceholder')" class="model-select" :disabled="!!saving || !!testing || fetchingModels">
                  <el-option v-for="m in embeddingModels" :key="m.id" :label="m.name" :value="m.id" />
                </el-select>
                <el-button type="primary" plain :loading="fetchingModels" @click="fetchRemoteModels" :disabled="!llmForm.api_key || !llmForm.api_base || !!saving || !!testing">
                  {{ t('common.btn.fetchModels') }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item :label="t('settings.llm.embeddingDim')">
              <el-input v-model="llmForm.embedding_dim" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.llm.jsonConfig')">
              <el-input v-model="llmJson" type="textarea" :rows="6" class="json-editor" :disabled="!!saving || !!testing" />
              <div class="json-actions">
                <el-button size="small" @click="syncJsonFromForm" :disabled="!!saving || !!testing">{{ t('settings.llm.jsonActions.syncFromForm') }}</el-button>
                <el-button size="small" @click="syncFormFromJson" :disabled="!!saving || !!testing">{{ t('settings.llm.jsonActions.syncFromJson') }}</el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <div class="form-actions">
                <el-button type="primary" :loading="saving === 'llm'" @click="saveCategory('llm', llmForm)">{{ t('common.btn.saveConfig') }}</el-button>
                <el-button :loading="testing === 'llm'" @click="testLLM">{{ t('common.btn.test') }}</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 数据库 -->
      <el-tab-pane :label="t('settings.tabs.database')" name="database">
        <div class="tab-content" v-loading="saving === 'database' || testing === 'database'" :element-loading-text="t('common.status.processing')">
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.database.host')">
              <el-input v-model="dbForm.host" placeholder="localhost" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.database.port')">
              <el-input v-model="dbForm.port" placeholder="5432" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.database.user')">
              <el-input v-model="dbForm.user" placeholder="knowledge" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.database.password')">
              <el-input v-model="dbForm.password" type="password" show-password :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.database.name')">
              <el-input v-model="dbForm.name" placeholder="knowledge" :disabled="!!saving || !!testing" />
            </el-form-item>
            <div class="url-preview">
              <span class="url-label">{{ t('common.label.connString') }}：</span>
              <code>postgresql+asyncpg://{{ dbForm.user }}:****@{{ dbForm.host }}:{{ dbForm.port }}/{{ dbForm.name }}</code>
            </div>
            <el-form-item>
              <div class="form-actions">
                <el-button type="primary" :loading="saving === 'database'" @click="saveDb">{{ t('common.btn.save') }}</el-button>
                <el-button :loading="testing === 'database'" @click="testCategory('database', dbForm)">{{ t('common.btn.test') }}</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- Redis -->
      <el-tab-pane :label="t('settings.tabs.redis')" name="redis">
        <div class="tab-content" v-loading="saving === 'redis' || testing === 'redis'" :element-loading-text="t('common.status.processing')">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
            <p>{{ t('settings.redis.info') }}</p>
          </el-alert>
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.redis.host')">
              <el-input v-model="redisForm.host" :placeholder="t('settings.redis.hostPlaceholder')" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.redis.port')">
              <el-input v-model="redisForm.port" :placeholder="t('settings.redis.portPlaceholder')" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.redis.password')">
              <el-input v-model="redisForm.password" type="password" show-password :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.redis.db')">
              <el-input v-model="redisForm.db" :placeholder="t('settings.redis.dbPlaceholder')" :disabled="!!saving || !!testing" />
            </el-form-item>
            <div class="url-preview" v-if="redisForm.host">
              <span class="url-label">{{ t('common.label.connString') }}：</span>
              <code>redis://{{ redisForm.password ? ':****@' : '' }}{{ redisForm.host }}:{{ redisForm.port }}/{{ redisForm.db }}</code>
            </div>
            <el-form-item>
              <div class="form-actions">
                <el-button type="primary" :loading="saving === 'redis'" @click="saveRedis">{{ t('common.btn.save') }}</el-button>
                <el-button :loading="testing === 'redis'" @click="testCategory('redis', redisForm)" :disabled="!redisForm.host">{{ t('common.btn.test') }}</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 向量库 -->
      <el-tab-pane :label="t('settings.tabs.milvus')" name="milvus">
        <div class="tab-content" v-loading="saving === 'milvus' || testing === 'milvus'" :element-loading-text="t('common.status.processing')">
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.milvus.host')">
              <el-input v-model="milvusForm.host" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.milvus.port')">
              <el-input v-model="milvusForm.port" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item :label="t('settings.milvus.collection')">
              <el-input v-model="milvusForm.collection" :disabled="!!saving || !!testing" />
            </el-form-item>
            <el-form-item>
              <div class="form-actions">
                <el-button type="primary" :loading="saving === 'milvus'" @click="saveCategory('milvus', milvusForm)">{{ t('common.btn.save') }}</el-button>
                <el-button :loading="testing === 'milvus'" @click="testCategory('milvus', milvusForm)">{{ t('common.btn.test') }}</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 安全 -->
      <el-tab-pane :label="t('settings.tabs.security')" name="security">
        <div class="tab-content" v-loading="saving === 'security'" :element-loading-text="t('common.status.saving')">
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.security.corsOrigins')">
              <el-input v-model="securityForm.cors_origins" :placeholder="t('settings.security.corsPlaceholder')" :disabled="!!saving" />
            </el-form-item>
            <el-form-item :label="t('settings.security.jwtAlgorithm')">
              <el-select v-model="securityForm.jwt_algorithm" :disabled="!!saving">
                <el-option label="RS256" value="RS256" />
                <el-option label="HS256" value="HS256" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving === 'security'" @click="saveCategory('security', securityForm)">{{ t('common.btn.save') }}</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- 账号安全 -->
      <el-tab-pane :label="t('settings.tabs.account')" name="account">
        <div class="tab-content" v-loading="saving === 'password'" :element-loading-text="t('common.status.saving')">
          <el-form label-position="top" class="settings-form">
            <el-form-item :label="t('settings.account.oldPassword')">
              <el-input v-model="pwdForm.old_password" type="password" :placeholder="t('settings.account.oldPasswordPlaceholder')" show-password :disabled="!!saving" />
            </el-form-item>
            <el-form-item :label="t('settings.account.newPassword')">
              <el-input v-model="pwdForm.new_password" type="password" :placeholder="t('settings.account.newPasswordPlaceholder')" show-password :disabled="!!saving" />
            </el-form-item>
            <el-form-item :label="t('settings.account.confirmPassword')">
              <el-input v-model="pwdForm.confirm_password" type="password" :placeholder="t('settings.account.confirmPlaceholder')" show-password :disabled="!!saving" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving === 'password'" @click="handleChangePassword">{{ t('settings.account.changeBtn') }}</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

const { t } = useI18n()
import {
  getCategoryConfig, updateCategoryConfig, testConnection,
  getLLMProviders, getProviderDefaultConfig, fetchModelsFromAPI
} from '@/api/system'
import request from '@/api/request'

const activeTab = ref('llm')
const providers = ref([])
const allModels = ref([])
const fetchingModels = ref(false)
const saving = ref(null)
const testing = ref(null)

const llmForm = reactive({ provider: '', api_key: '', api_base: '', model: '', embedding_model: '', embedding_dim: '1536' })
const dbForm = reactive({ host: 'localhost', port: '5432', user: 'knowledge', password: '', name: 'knowledge' })
const redisForm = reactive({ host: '', port: '6379', password: '', db: '0' })
const milvusForm = reactive({ host: '', port: '', collection: '' })
const securityForm = reactive({ cors_origins: '', jwt_algorithm: 'RS256' })
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const llmJson = ref('{}')

const chatModels = computed(() => allModels.value.filter(m => m.type === 'chat'))
const embeddingModels = computed(() => allModels.value.filter(m => m.type === 'embedding'))

onMounted(async () => {
  providers.value = await getLLMProviders()
  await loadConfigs()
})

async function loadConfigs() {
  try {
    const llm = await getCategoryConfig('llm')
    Object.assign(llmForm, llm)
    syncJsonFromForm()
    if (llm.provider) await onProviderChange(llm.provider)

    // 解析 database URL 回填到字段
    const db = await getCategoryConfig('database')
    if (db.url) parseDbUrl(db.url)
    else if (db.host) Object.assign(dbForm, db)

    // 解析 redis URL 回填到字段
    const redis = await getCategoryConfig('redis')
    if (redis.url) parseRedisUrl(redis.url)
    else if (redis.host) Object.assign(redisForm, redis)

    const milvus = await getCategoryConfig('milvus')
    Object.assign(milvusForm, milvus)

    const sec = await getCategoryConfig('security')
    Object.assign(securityForm, sec)
  } catch {}
}

function parseDbUrl(url) {
  // postgresql+asyncpg://user:pass@host:port/db
  try {
    const m = url.match(/\/\/([^:]+):([^@]+)@([^:]+):(\d+)\/(.+)/)
    if (m) {
      dbForm.user = m[1]
      dbForm.password = m[2]
      dbForm.host = m[3]
      dbForm.port = m[4]
      dbForm.name = m[5]
    }
  } catch {}
}

function parseRedisUrl(url) {
  // redis://[:pass@]host:port/db
  try {
    const m = url.match(/redis:\/\/(?::([^@]+)@)?([^:]+):(\d+)\/(\d+)/)
    if (m) {
      redisForm.password = m[1] || ''
      redisForm.host = m[2]
      redisForm.port = m[3]
      redisForm.db = m[4]
    }
  } catch {}
}

function syncJsonFromForm() { llmJson.value = JSON.stringify(llmForm, null, 2) }
function syncFormFromJson() {
  try { Object.assign(llmForm, JSON.parse(llmJson.value)); ElMessage.success(t('common.msg.syncSuccess')) }
  catch { ElMessage.error(t('common.msg.jsonFormatError')) }
}

async function onProviderChange(name) {
  try {
    const defaults = await getProviderDefaultConfig(name)
    if (!llmForm.api_base) llmForm.api_base = defaults.api_base || ''
    if (!llmForm.model) llmForm.model = defaults.model || ''
    if (!llmForm.embedding_model) llmForm.embedding_model = defaults.embedding_model || ''
    allModels.value = []
  } catch { allModels.value = [] }
}

async function fetchRemoteModels() {
  if (!llmForm.api_key || !llmForm.api_base) { ElMessage.warning(t('setup.llm.fetchWarning')); return }
  fetchingModels.value = true
  try {
    const result = await fetchModelsFromAPI(llmForm.provider, llmForm.api_key, llmForm.api_base)
    allModels.value = result.models || []
    ElMessage.success(t('setup.llm.fetchSuccess', { total: result.total }))
  } catch { ElMessage.error(t('common.msg.fetchFailed')) }
  finally { fetchingModels.value = false }
}

function assembleDbUrl() {
  return `postgresql+asyncpg://${dbForm.user}:${dbForm.password}@${dbForm.host}:${dbForm.port}/${dbForm.name}`
}
function assembleRedisUrl() {
  if (!redisForm.host) return ''
  if (redisForm.password) return `redis://:${redisForm.password}@${redisForm.host}:${redisForm.port}/${redisForm.db}`
  return `redis://${redisForm.host}:${redisForm.port}/${redisForm.db}`
}

async function saveDb() {
  saving.value = 'database'
  try { await saveCategory('database', { url: assembleDbUrl() }) }
  finally { saving.value = null }
}
async function saveRedis() {
  saving.value = 'redis'
  try {
    if (!redisForm.host) await saveCategory('redis', { url: '' })
    else await saveCategory('redis', { url: assembleRedisUrl() })
  } finally { saving.value = null }
}

async function saveCategory(category, data) {
  saving.value = category
  try {
    await updateCategoryConfig(category, data)
    ElMessage.success(t('common.msg.saveSuccess'))
  } catch { ElMessage.error(t('common.msg.saveFailed')) }
  finally { saving.value = null }
}

async function testCategory(category, data) {
  testing.value = category
  try {
    const result = await testConnection(category, data)
    result.success ? ElMessage.success(result.message) : ElMessage.error(result.message)
  } catch { ElMessage.error(t('common.msg.testFailed')) }
  finally { testing.value = null }
}

async function testLLM() { await testCategory('llm', llmForm) }

async function handleChangePassword() {
  if (!pwdForm.old_password || !pwdForm.new_password) { ElMessage.warning(t('settings.account.pwdRequired')); return }
  if (pwdForm.new_password.length < 6) { ElMessage.warning(t('settings.account.pwdAtLeast')); return }
  if (pwdForm.new_password !== pwdForm.confirm_password) { ElMessage.warning(t('settings.account.pwdMismatch')); return }
  saving.value = 'password'
  try {
    await request.post('/auth/change-password', { old_password: pwdForm.old_password, new_password: pwdForm.new_password })
    ElMessage.success(t('settings.account.pwdSuccess'))
    pwdForm.old_password = ''; pwdForm.new_password = ''; pwdForm.confirm_password = ''
  } catch {}
  finally { saving.value = null }
}
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: var(--font-size-2xl); }
.page-header p { color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.settings-tabs { background: var(--color-bg-card); border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); padding: 24px; }
.tab-content { max-width: 600px; padding-top: 16px; }
.settings-form :deep(.el-form-item) { margin-bottom: 20px; }
.form-actions { display: flex; gap: 12px; }
.provider-option { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.model-input-row { display: flex; gap: 8px; width: 100%; }
.model-select { flex: 1; }
.el-select { width: 100%; }
.json-editor :deep(textarea) { font-family: 'Cascadia Code', monospace; font-size: 13px; }
.json-actions { margin-top: 6px; display: flex; gap: 8px; }
.url-preview { background: #f0f0f0; padding: 8px 12px; border-radius: var(--radius-md); margin-bottom: 16px; font-size: 13px; }
.url-label { color: var(--color-text-secondary); }
.url-preview code { color: #7C3AED; font-family: 'Cascadia Code', monospace; }
</style>
