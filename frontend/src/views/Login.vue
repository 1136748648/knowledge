<template>
  <div class="login-page">
    <!-- Language switcher -->
    <div class="lang-bar">
      <el-dropdown trigger="click" @command="switchLang">
        <el-button text size="small" class="lang-btn">
          <el-icon><Switch /></el-icon>
          {{ currentLangLabel }}
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="zh-CN">中文</el-dropdown-item>
            <el-dropdown-item command="en-US">English</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- Loading overlay -->
    <Transition name="fade">
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner">
          <div class="spinner"></div>
          <p>{{ t('login.loggingIn') }}</p>
        </div>
      </div>
    </Transition>

    <div class="login-card fade-in">
      <div class="login-header">
        <el-icon :size="40" color="#7C3AED"><Connection /></el-icon>
        <h1>{{ t('login.title') }}</h1>
        <p>{{ t('login.subtitle') }}</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item :label="t('login.username')" prop="username">
          <el-input v-model="form.username" :placeholder="t('login.usernamePlaceholder')" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item :label="t('login.password')" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="t('login.passwordPlaceholder')"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="rememberMe">{{ t('login.remember') }}</el-checkbox>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
            {{ t('login.login') }}
          </el-button>
        </el-form-item>
      </el-form>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'

const { t, locale } = useI18n()
const currentLangLabel = computed(() => locale.value === 'en-US' ? 'English' : '中文')

function switchLang(lang) {
  locale.value = lang
  localStorage.setItem('kp_lang', lang)
}

const REMEMBER_KEY = 'kp_remember'
const REMEMBER_DAYS = 30

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
})

// 页面加载时恢复记住的账号密码
onMounted(() => {
  try {
    const raw = localStorage.getItem(REMEMBER_KEY)
    if (!raw) return
    const data = JSON.parse(raw)
    if (data.expires < Date.now()) {
      localStorage.removeItem(REMEMBER_KEY)
      return
    }
    form.username = data.username || ''
    form.password = atob(data.password || '')
    rememberMe.value = true
  } catch {}
})

function saveRemember() {
  if (rememberMe.value) {
    const expires = Date.now() + REMEMBER_DAYS * 24 * 60 * 60 * 1000
    localStorage.setItem(REMEMBER_KEY, JSON.stringify({
      username: form.username,
      password: btoa(form.password),
      expires,
    }))
  } else {
    localStorage.removeItem(REMEMBER_KEY)
  }
}

const rules = {
  username: [{ required: true, message: t('login.usernamePlaceholder'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordPlaceholder'), trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await request.post('/auth/token', {
      username: form.username,
      password: form.password,
    })
    userStore.setToken(data.access_token)
    saveRemember()

    // 获取用户信息
    const user = await request.get('/auth/me')

    // 检查系统是否已初始化
    try {
      const status = await request.get('/system/status')
      if (!status.initialized) {
        if (user.username === 'builtin-admin') {
          ElMessage.success(t('login.setupRedirect'))
          router.push('/setup')
        } else {
          ElMessage.warning(t('login.systemNotInit'))
          userStore.logout()
        }
        return
      }
    } catch {
      // 无法获取状态，进入主页面
    }

    ElMessage.success(t('login.loginSuccess'))
    router.push('/')
  } catch (e) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #F5F3FF 0%, #FAF5FF 50%, #FFF7ED 100%);
  position: relative;
}

.lang-bar {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-sm);
}

/* Loading overlay */
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.loading-spinner {
  text-align: center;
}

.loading-spinner p {
  margin-top: 16px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E9D5FF;
  border-top-color: #7C3AED;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.login-card {
  background: white;
  border-radius: var(--radius-2xl);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-xl);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin-top: 12px;
  font-size: var(--font-size-2xl);
}

.login-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  margin-top: 4px;
}

.login-options {
  display: flex;
  align-items: center;
  width: 100%;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: var(--font-size-base);
}
</style>
