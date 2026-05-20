<template>
  <div class="qa-page fade-in">
    <div class="page-header">
      <h1>{{ t('qa.title') }}</h1>
      <p>{{ t('qa.subtitle') }}</p>
    </div>

    <div class="qa-container">
      <!-- 消息列表 -->
      <div ref="messagesRef" class="messages-area">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon :size="64" color="#E5E7EB"><ChatDotRound /></el-icon>
          <h3>{{ t('qa.emptyTitle') }}</h3>
          <p>{{ t('qa.emptyDesc') }}</p>
          <div class="suggestions">
            <el-button v-for="s in suggestions" :key="s" text class="suggestion-btn" @click="sendMessage(s)">
              {{ s }}
            </el-button>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="36" class="user-avatar">U</el-avatar>
            <el-avatar v-else :size="36" class="ai-avatar">
              <el-icon :size="20"><MagicStick /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="msg.content" />
            <div v-if="msg.sources?.length" class="message-sources">
              <el-divider />
              <div class="sources-label">{{ t('qa.sourceLabel') }}：</div>
              <el-tag v-for="s in msg.sources" :key="s" size="small" type="info">
                {{ s.type === 'database' ? `${t('dashboard.systemStatus.database')} · ${s.table}` : s.title || s.type }}
              </el-tag>
            </div>
          </div>
        </div>

        <div v-if="loading" class="message ai">
          <div class="message-avatar">
            <el-avatar :size="36" class="ai-avatar">
              <el-icon :size="20"><MagicStick /></el-icon>
            </el-avatar>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <el-input
          v-model="input"
          :placeholder="t('qa.inputPlaceholder')"
          size="large"
          :disabled="loading"
          @keyup.enter="sendMessage(input)"
        >
          <template #append>
            <el-button :icon="'Promotion'" type="primary" :loading="loading" @click="sendMessage(input)" />
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { askQuestion } from '@/api/qa'

const { t } = useI18n()
const input = ref('')
const loading = ref(false)
const messages = ref([])
const messagesRef = ref(null)

const suggestions = computed(() => [
  t('qa.suggestions.0'),
  t('qa.suggestions.1'),
  t('qa.suggestions.2'),
  t('qa.suggestions.3'),
])

async function sendMessage(text) {
  if (!text?.trim() || loading.value) return

  const question = text.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: question })

  loading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const resp = await askQuestion(question)
    messages.value.push({
      role: 'ai',
      content: resp.answer,
      sources: resp.sources,
    })
  } catch (e) {
    messages.value.push({
      role: 'ai',
      content: t('qa.errorMsg'),
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-header h1 { font-size: var(--font-size-2xl); }
.page-header p { color: var(--color-text-secondary); font-size: var(--font-size-sm); }

.qa-container {
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-light);
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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
.empty-state p { margin-top: 8px; color: var(--color-text-secondary); font-size: var(--font-size-sm); }

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 24px;
  justify-content: center;
}

.suggestion-btn {
  border: 1px solid var(--color-border) !important;
  border-radius: var(--radius-full) !important;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  background: var(--color-primary-50);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
}

.message.user .message-content {
  background: var(--color-primary);
  color: white;
}

.message-text {
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.message-sources {
  margin-top: 8px;
}

.message-sources .el-divider {
  margin: 8px 0;
}

.sources-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.user-avatar {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}

.ai-avatar {
  background: var(--color-primary-100);
  color: var(--color-primary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-primary-light);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--color-border-light);
}

.input-area :deep(.el-input-group__append) {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}
</style>
