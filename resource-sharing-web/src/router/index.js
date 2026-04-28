import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    { path: '/', component: () => import('../views/Login.vue') }, // 我们要把 App.vue 的内容搬到 Login.vue
    { path: '/home', component: () => import('../views/Home.vue') },
    { path: '/users', component: () => import('../views/UserManagement.vue') },
    { path: '/statistics', component: () => import('../views/Statistics.vue') }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')

    // 需要登录的页面
    const authPages = ['/home', '/users', '/statistics']
    if (authPages.includes(to.path) && !token) {
        next('/')
        return
    }

    next()
})

export default router