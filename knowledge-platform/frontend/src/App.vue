<template>
  <el-config-provider :locale="elLocale">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import enUs from 'element-plus/es/locale/lang/en'

const { locale } = useI18n()

const elLocale = computed(() => locale.value === 'en-US' ? enUs : zhCn)
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
