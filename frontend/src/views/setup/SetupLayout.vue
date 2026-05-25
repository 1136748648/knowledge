<template>
  <div class="setup-page">
    <div class="setup-card fade-in">
      <div class="setup-header">
        <el-icon :size="40" color="#7C3AED"><Connection /></el-icon>
        <h1>{{ t('setup.title') }}</h1>
        <p>{{ t('setup.subtitle') }}</p>
      </div>

      <el-steps :active="currentStep" finish-status="success" class="steps">
        <el-step :title="t('setup.steps.database')" icon="Coin" />
        <el-step :title="t('setup.steps.redis')" icon="Coin" />
        <el-step :title="t('setup.steps.milvus')" icon="Compass" />
        <el-step :title="t('setup.steps.storage')" icon="Folder" />
        <el-step :title="t('setup.steps.llm')" icon="MagicStick" />
        <el-step :title="t('setup.steps.admin')" icon="User" />
      </el-steps>

      <div class="step-content" v-loading="testing" :element-loading-text="t('common.status.testing')">
        <!-- Step 0: PostgreSQL -->
        <div v-if="currentStep === 0">
          <el-form label-position="top">
            <el-form-item :label="t('setup.database.host')">
              <el-input v-model="form.database.host" :placeholder="t('setup.database.hostPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.database.port')">
              <el-input v-model="form.database.port" :placeholder="t('setup.database.portPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.database.user')">
              <el-input v-model="form.database.user" :placeholder="t('setup.database.userPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.database.password')">
              <el-input v-model="form.database.password" type="password" :placeholder="t('setup.database.passwordPlaceholder')" show-password :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.database.name')">
              <el-input v-model="form.database.name" :placeholder="t('setup.database.namePlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <div class="url-preview" v-if="form.database.host">
              <span class="url-label">{{ t('common.label.connString') }}：</span>
              <code>{{ assembledDbUrl }}</code>
            </div>
            <el-button type="primary" :loading="testing === 'database'" @click="testConnection('database')">
              <el-icon><Connection /></el-icon> {{ t('setup.database.testBtn') }}
            </el-button>
          </el-form>

          <el-divider />
          <el-collapse>
            <el-collapse-item :title="t('setup.database.installGuide')" name="pg">
              <div class="guide-content">
                <p><strong>{{ t('setup.database.dockerInstall') }}：</strong></p>
                <div class="code-inline">docker run -d --name pg -e POSTGRES_USER=knowledge -e POSTGRES_PASSWORD=knowledge123 -e POSTGRES_DB=knowledge -p 5432:5432 postgres:15</div>
                <p>{{ t('setup.database.website') }}：<a href="https://www.postgresql.org" target="_blank">postgresql.org</a></p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Step 1: Redis（可选） -->
        <div v-if="currentStep === 1">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
            <template #title>{{ t('setup.redis.infoTitle') }}</template>
            <template #default>
              <p>{{ t('setup.redis.infoDesc') }}</p>
            </template>
          </el-alert>

          <el-form label-position="top">
            <el-form-item :label="t('setup.redis.host')">
              <el-input v-model="form.redis.host" :placeholder="t('setup.redis.hostPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.redis.port')">
              <el-input v-model="form.redis.port" :placeholder="t('setup.redis.portPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.redis.password')">
              <el-input v-model="form.redis.password" type="password" :placeholder="t('setup.redis.passwordPlaceholder')" show-password :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.redis.db')">
              <el-input v-model="form.redis.db" :placeholder="t('setup.redis.dbPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <div class="url-preview" v-if="form.redis.host">
              <span class="url-label">{{ t('common.label.connString') }}：</span>
              <code>{{ assembledRedisUrl }}</code>
            </div>
            <el-button type="primary" :loading="testing === 'redis'" @click="testConnection('redis')" :disabled="!form.redis.host">
              <el-icon><Connection /></el-icon> {{ t('setup.redis.testBtn') }}
            </el-button>
          </el-form>

          <el-divider />
          <el-collapse>
            <el-collapse-item :title="t('setup.redis.installGuide')" name="redis">
              <div class="guide-content">
                <p><strong>{{ t('setup.redis.dockerInstall') }}：</strong></p>
                <div class="code-inline">docker run -d --name redis -p 6379:6379 redis:7</div>
                <p>{{ t('setup.redis.website') }}：<a href="https://redis.io" target="_blank">redis.io</a></p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Step 2: Milvus -->
        <div v-if="currentStep === 2">
          <el-form label-position="top">
            <el-form-item :label="t('setup.milvus.host')">
              <el-input v-model="form.milvus.host" :placeholder="t('setup.milvus.hostPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.milvus.port')">
              <el-input v-model="form.milvus.port" :placeholder="t('setup.milvus.portPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.milvus.collection')">
              <el-input v-model="form.milvus.collection" :placeholder="t('setup.milvus.collectionPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-button type="primary" :loading="testing === 'milvus'" @click="testConnection('milvus')">
              <el-icon><Connection /></el-icon> {{ t('setup.milvus.testBtn') }}
            </el-button>
          </el-form>

          <el-divider />
          <el-collapse>
            <el-collapse-item :title="t('setup.milvus.installGuide')" name="milvus">
              <div class="guide-content">
                <p><strong>{{ t('setup.milvus.dockerInstall') }}：</strong></p>
                <div class="code-inline">docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest</div>
                <p>{{ t('setup.milvus.website') }}：<a href="https://milvus.io" target="_blank">milvus.io</a></p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Step 3: Storage -->
        <div v-if="currentStep === 3">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px">
            <template #title>{{ t('setup.storage.infoTitle') }}</template>
            <template #default>
              <p>{{ t('setup.storage.infoDesc') }}</p>
            </template>
          </el-alert>

          <el-form label-position="top">
            <el-form-item :label="t('setup.storage.provider')">
              <el-select v-model="form.storage.provider" :disabled="!!testing">
                <el-option v-for="(label, key) in t('setup.storage.providers')" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
            <el-form-item :label="t('setup.storage.host')">
              <el-input v-model="form.storage.host" :placeholder="t('setup.storage.hostPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.storage.port')">
              <el-input v-model="form.storage.port" :placeholder="t('setup.storage.portPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.storage.bucket')">
              <el-input v-model="form.storage.bucket" :placeholder="t('setup.storage.bucketPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.storage.accessKey')">
              <el-input v-model="form.storage.access_key" :placeholder="t('setup.storage.accessKeyPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.storage.secretKey')">
              <el-input v-model="form.storage.secret_key" type="password" :placeholder="t('setup.storage.secretKeyPlaceholder')" show-password :disabled="!!testing" />
            </el-form-item>
            <el-button type="primary" :loading="testing === 'storage'" @click="testConnection('storage')" :disabled="!form.storage.host">
              <el-icon><Connection /></el-icon> {{ t('setup.storage.testBtn') }}
            </el-button>
          </el-form>

          <el-divider />
          <el-collapse>
            <el-collapse-item :title="t('setup.storage.installGuide')" name="storage">
              <div class="guide-content">
                <p><strong>{{ t('setup.storage.dockerInstall') }}：</strong></p>
                <div class="code-inline">docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"</div>
                <p>{{ t('setup.storage.website') }}：<a href="https://min.io" target="_blank">min.io</a></p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Step 4: LLM -->
        <div v-if="currentStep === 4">
          <el-form label-position="top">
            <el-form-item :label="t('setup.llm.provider')">
              <el-select v-model="form.llm.provider" filterable allow-create :placeholder="t('setup.llm.providerPlaceholder')" @change="onProviderChange" :disabled="!!testing">
                <el-option v-for="p in providers" :key="p.name" :label="p.display_name" :value="p.name" />
              </el-select>
            </el-form-item>
            <el-form-item :label="t('setup.llm.apiKey')">
              <el-input v-model="form.llm.api_key" :placeholder="t('setup.llm.apiKeyPlaceholder')" show-password :disabled="!!testing" />
            </el-form-item>
            <el-form-item :label="t('setup.llm.apiBase')">
              <el-input v-model="form.llm.api_base" :placeholder="t('setup.llm.apiBasePlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <el-form-item v-if="currentProvider.supports_chat !== false" :label="t('setup.llm.chatModel')">
              <el-input v-model="form.llm.model" :placeholder="t('setup.llm.modelPlaceholder')" :disabled="!!testing" />
            </el-form-item>
            <template v-if="currentProvider.supports_embedding !== false">
              <el-form-item :label="t('setup.llm.embeddingModel')">
                <el-input v-model="form.llm.embedding_model" :placeholder="t('setup.llm.embeddingModelPlaceholder')" :disabled="!!testing" />
              </el-form-item>
              <el-form-item :label="t('setup.llm.embeddingDim')">
                <el-input v-model="form.llm.embedding_dim" :placeholder="t('setup.llm.embeddingDimPlaceholder')" :disabled="!!testing" />
              </el-form-item>
            </template>
            <el-button type="primary" :loading="testing === 'llm'" @click="testConnection('llm')">
              <el-icon><Connection /></el-icon> {{ t('setup.llm.testBtn') }}
            </el-button>
          </el-form>

          <!-- JSON 配置 -->
          <el-divider />
          <div class="json-config-section">
            <div class="json-header">
              <span class="json-title">{{ t('setup.llm.jsonConfig') }}</span>
              <el-button text size="small" @click="syncJsonFromForm">{{ t('common.btn.syncFromForm') }}</el-button>
            </div>
            <el-input v-model="llmJson" type="textarea" :rows="8" class="json-editor" :disabled="!!testing" />
            <p class="json-hint">{{ t('setup.llm.jsonHint') }}</p>
            <el-button size="small" @click="syncFormFromJson" :disabled="!!testing">{{ t('common.btn.syncFromJson') }}</el-button>
          </div>

          <el-divider />
          <div v-if="currentProviderGuide">
            <el-collapse>
              <el-collapse-item :title="`${currentProvider.display_name} - ${t('setup.llm.note')}`" name="provider">
                <div class="guide-content">
                  <p><strong>{{ t('setup.llm.installSdk') }}：</strong></p>
                  <div class="code-inline">{{ currentProviderGuide.install }}</div>
                  <p><strong>{{ t('setup.llm.note') }}：</strong>{{ currentProviderGuide.note }}</p>
                  <p>{{ t('setup.llm.website') }}：<a :href="currentProviderGuide.website" target="_blank">{{ currentProviderGuide.website }}</a></p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <!-- Step 5: 管理员 -->
        <div v-if="currentStep === 5">
          <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 20px">
            <template #title>{{ t('setup.admin.alertTitle') }}</template>
            <template #default>
              <p>{{ t('setup.admin.alertDesc', { user: 'builtin-admin' }) }}</p>
            </template>
          </el-alert>

          <el-form label-position="top">
            <el-form-item :label="t('setup.admin.adminUsername')">
              <el-input value="admin" disabled />
            </el-form-item>
            <el-form-item :label="t('setup.admin.adminPassword')" :error="passwordError">
              <el-input v-model="adminPassword" type="password" :placeholder="t('setup.admin.passwordPlaceholder')" show-password :disabled="submitting" />
            </el-form-item>
            <el-form-item :label="t('common.field.confirmPassword')" :error="confirmError">
              <el-input v-model="adminPasswordConfirm" type="password" :placeholder="t('setup.admin.confirmPlaceholder')" show-password :disabled="submitting" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="currentStep--">{{ t('common.btn.back') }}</el-button>
        <el-button v-if="currentStep < 5" type="primary" @click="nextStep">{{ t('common.btn.next') }}</el-button>
        <el-button v-if="currentStep === 5" type="primary" :loading="submitting" @click="handleInit">
          {{ t('common.btn.submit') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getLLMProviders, getProviderDefaultConfig, testConnection as testApi,
  initSystem,
} from '@/api/system'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const { t } = useI18n()
const currentStep = ref(0)
const submitting = ref(false)
const testing = ref(null)
const providers = ref([])
const adminPassword = ref('')
const adminPasswordConfirm = ref('')
const passwordError = ref('')
const confirmError = ref('')

const form = reactive({
  database: { host: '', port: '', user: '', password: '', name: '' },
  redis: { host: '', port: '', password: '', db: '0' },
  milvus: { host: '', port: '', collection: '' },
  storage: { provider: 'minio', host: '', port: '', access_key: '', secret_key: '', bucket: '' },
  llm: { provider: '', api_key: '', api_base: '', model: '', embedding_model: '', embedding_dim: '' },
  keycloak: { server_url: '', realm: '', client_id: '', client_secret: '' },
  security: { cors_origins: '', jwt_algorithm: 'RS256' },
  audit: { enabled: 'true' },
})

const llmJson = ref('')

const currentProvider = computed(() => providers.value.find(p => p.name === form.llm.provider) || {})
const currentProviderGuide = computed(() => {
  const p = currentProvider.value
  if (!p.website) return null
  return { website: p.website, install: p.install_guide, note: p.note }
})

const assembledDbUrl = computed(() => {
  const d = form.database
  if (!d.host) return ''
  const port = d.port || '5432'
  const user = d.user || ''
  const password = d.password ? ':' + d.password : ''
  const name = d.name || ''
  return `postgresql://${user}${password}@${d.host}:${port}/${name}`
})

const assembledRedisUrl = computed(() => {
  const r = form.redis
  if (!r.host) return ''
  const port = r.port || '6379'
  const db = r.db || '0'
  if (r.password) return `redis://:${r.password}@${r.host}:${port}/${db}`
  return `redis://${r.host}:${port}/${db}`
})

watch(() => ({ ...form.llm }), () => { syncJsonFromForm() }, { deep: true })

onMounted(async () => {
  providers.value = await getLLMProviders()
  if (providers.value.length > 0) {
    form.llm.provider = providers.value[0].name
    await onProviderChange(form.llm.provider)
  }
  syncJsonFromForm()
})

function syncJsonFromForm() { llmJson.value = JSON.stringify(form.llm, null, 2) }

function syncFormFromJson() {
  try {
    Object.assign(form.llm, JSON.parse(llmJson.value))
    ElMessage.success(t('common.msg.syncSuccess'))
  } catch { ElMessage.error(t('common.msg.jsonFormatError')) }
}

async function onProviderChange(name) {
  try {
    const defaults = await getProviderDefaultConfig(name)
    form.llm.api_base = defaults.api_base || ''
    form.llm.model = defaults.model || ''
    form.llm.embedding_model = defaults.embedding_model || ''
    form.llm.embedding_dim = defaults.embedding_dim || ''
  } catch {}
}

async function testConnection(type) {
  testing.value = type
  try {
    const configs = type === 'llm' ? { ...form.llm } : { ...form[type] }
    const result = await testApi(type, configs)
    if (result.success) {
      const successMessages = {
        database: t('setup.database.testSuccess'),
        redis: t('setup.redis.testSuccess'),
        milvus: t('setup.milvus.testSuccess'),
        storage: t('setup.storage.testSuccess'),
        llm: t('setup.llm.testSuccess'),
      }
      ElMessage.success(successMessages[type] || result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch { ElMessage.error(t('common.msg.testFailed')) }
  finally { testing.value = null }
}

function nextStep() { currentStep.value++ }

async function handleInit() {
  passwordError.value = ''
  confirmError.value = ''
  if (!adminPassword.value || adminPassword.value.length < 6) { passwordError.value = t('setup.admin.passwordAtLeast'); return }
  if (adminPassword.value !== adminPasswordConfirm.value) { confirmError.value = t('setup.admin.passwordMismatch'); return }

  try {
    await ElMessageBox.confirm(
      t('setup.init.confirmMsg'),
      t('setup.init.confirmTitle'),
      { confirmButtonText: t('setup.init.confirmBtn'), cancelButtonText: t('setup.init.cancelBtn'), type: 'warning' },
    )
  } catch { return }

  submitting.value = true
  try {
    await initSystem({ ...form, admin_password: adminPassword.value })
    ElMessage.success(t('setup.init.successMsg'))
    userStore.logout()
    await ElMessageBox.alert(t('setup.init.successNote'), t('setup.init.successTitle'), {
      confirmButtonText: t('common.btn.goLogin'),
    })
    router.push('/login')
  } catch { ElMessage.error(t('setup.init.failedMsg')) }
  finally { submitting.value = false }
}
</script>

<style scoped>
.setup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #F5F3FF 0%, #FAF5FF 50%, #FFF7ED 100%);
  padding: 24px;
}
.setup-card { background: white; border-radius: var(--radius-2xl); padding: 40px; width: 100%; max-width: 680px; box-shadow: var(--shadow-xl); }
.setup-header { text-align: center; margin-bottom: 32px; }
.setup-header h1 { margin-top: 12px; font-size: var(--font-size-2xl); }
.setup-header p { color: var(--color-text-secondary); font-size: var(--font-size-sm); margin-top: 4px; }
.steps { margin-bottom: 32px; }
.step-content { min-height: 280px; }
.guide-content { font-size: var(--font-size-sm); line-height: 1.8; }
.guide-content a { color: var(--color-primary); text-decoration: none; }
.guide-content a:hover { text-decoration: underline; }
.code-inline { background: #1e1e2e; color: #cdd6f4; padding: 8px 12px; border-radius: var(--radius-md); font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 13px; margin: 6px 0; overflow-x: auto; }
.step-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
.el-select { width: 100%; }

.url-preview {
  background: #f0f0f0;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  font-size: 13px;
  word-break: break-all;
}
.url-label { color: var(--color-text-secondary); margin-right: 4px; }
.url-preview code { color: #7C3AED; font-family: 'Cascadia Code', monospace; }

.json-config-section { background: #f8f9fa; border-radius: var(--radius-md); padding: 16px; }
.json-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.json-title { font-weight: 600; font-size: var(--font-size-sm); }
.json-editor :deep(textarea) { font-family: 'Cascadia Code', monospace; font-size: 13px; line-height: 1.5; }
.json-hint { font-size: 12px; color: var(--color-text-secondary); margin: 6px 0; }
</style>
