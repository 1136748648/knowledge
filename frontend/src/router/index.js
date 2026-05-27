import { createRouter, createWebHistory } from 'vue-router'
import { getUserInfo } from '@/api/auth'
import { getSystemStatus } from '@/api/system'

const routes = [
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('@/views/setup/SetupLayout.vue'),
    meta: { requiresAuth: true, requiresBuiltinAdmin: true },
  },
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'qa',
        name: 'QA',
        component: () => import('@/views/QA.vue'),
      },
      {
        path: 'heatmap',
        name: 'Heatmap',
        component: () => import('@/views/Heatmap.vue'),
      },
      {
        path: 'admin/settings',
        name: 'Settings',
        component: () => import('@/views/admin/Settings.vue'),
        meta: { requiresAdmin: true },
      },
      {
        path: 'trace',
        name: 'Trace',
        component: () => import('@/views/Trace.vue'),
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

async function checkSystemInitialized() {
  try {
    const data = await getSystemStatus()
    return data.initialized
  } catch {
    return true
  }
}

async function checkBuiltinAdmin(token) {
  try {
    const user = await getUserInfo(token)
    return user.username === 'builtin-admin'
  } catch {
    return false
  }
}

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.path === '/login') {
    if (token) {
      const initialized = await checkSystemInitialized()
      if (initialized) {
        next('/')
      } else {
        const isBuiltinAdmin = await checkBuiltinAdmin(token)
        if (isBuiltinAdmin) {
          next('/setup')
        } else {
          localStorage.removeItem('token')
          next()
        }
      }
    } else {
      next()
    }
    return
  }

  const initialized = await checkSystemInitialized()

  if (!initialized && to.path !== '/setup') {
    if (!token) {
      next('/login')
      return
    }
    const isBuiltinAdmin = await checkBuiltinAdmin(token)
    if (isBuiltinAdmin) {
      next('/setup')
    } else {
      next('/login')
    }
    return
  }

  if (to.meta.requiresAuth !== false) {
    if (!token) {
      next('/login')
      return
    }

    if (to.meta.requiresBuiltinAdmin) {
      const isBuiltinAdmin = await checkBuiltinAdmin(token)
      if (!isBuiltinAdmin) {
        next('/')
        return
      }
    }
  }

  next()
})

export default router
