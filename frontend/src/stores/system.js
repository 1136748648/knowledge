import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSystemStatus, getAllConfigs, getLLMProviders } from '@/api/system'

export const useSystemStore = defineStore('system', () => {
  const initialized = ref(false)
  const loading = ref(false)
  const configs = ref({})
  const providers = ref([])

  async function checkStatus() {
    try {
      const data = await getSystemStatus()
      initialized.value = data.initialized
      return data
    } catch (e) {
      initialized.value = false
      return { initialized: false }
    }
  }

  async function fetchConfigs() {
    loading.value = true
    try {
      configs.value = await getAllConfigs()
    } finally {
      loading.value = false
    }
  }

  async function fetchProviders() {
    providers.value = await getLLMProviders()
  }

  return { initialized, loading, configs, providers, checkStatus, fetchConfigs, fetchProviders }
})
