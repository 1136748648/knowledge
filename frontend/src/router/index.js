import { createRouter, createWebHistory } from 'vue-router'

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
        path: 'wiki',
        name: 'Wiki',
        component: () => import('@/views/Wiki.vue'),
      },
      {
        path: 'qa',
        name: 'QA',
        component: () => import('@/views/QA.vue'),
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
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
        path: 'admin/tags',
        name: 'TagsManager',
        component: () => import('@/views/admin/TagsManager.vue'),
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

router.beforeEach(async (to, from, next) => {
  // 跳过登录页本身
  if (to.path === '/login') {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const statusResp = await fetch('/api/system/status')
        const status = await statusResp.json()
        if (status.initialized) {
          next('/')
        } else {
          // 系统未初始化 → 检查是否为内置管理员
          const meResp = await fetch('/api/auth/me', {
            headers: { Authorization: `Bearer ${token}` },
          })
          if (meResp.ok) {
            const user = await meResp.json()
            next(user.username === 'builtin-admin' ? '/setup' : '/')
          } else {
            localStorage.removeItem('token')
            next()
          }
        }
      } catch {
        next('/')
      }
      return
    }
    next()
    return
  }

  // 检查系统初始化状态
  let initialized = true
  try {
    const resp = await fetch('/api/system/status')
    const data = await resp.json()
    initialized = data.initialized
  } catch {
    // API 不可用，继续
  }

  // 未初始化且不在 setup 页面 → 去登录
  if (!initialized && to.path !== '/setup') {
    const token = localStorage.getItem('token')
    if (!token) {
      next('/login')
      return
    }
    // 有 token → 检查是否为内置管理员
    try {
      const meResp = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (meResp.ok) {
        const user = await meResp.json()
        if (user.username === 'builtin-admin') {
          next('/setup')
          return
        }
      }
    } catch {}
    // 非内置管理员 → 回登录页
    next('/login')
    return
  }

  // 需要登录的页面检查 token
  if (to.meta.requiresAuth !== false) {
    const token = localStorage.getItem('token')
    if (!token) {
      next('/login')
      return
    }

    // /setup 页面：仅内置管理员可访问
    if (to.meta.requiresBuiltinAdmin) {
      try {
        const resp = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!resp.ok) {
          localStorage.removeItem('token')
          next('/login')
          return
        }
        const user = await resp.json()
        if (user.username !== 'builtin-admin') {
          next('/')
          return
        }
      } catch {
        next('/login')
        return
      }
    }
  }

  next()
})

export default router
