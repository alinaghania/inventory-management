import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Routes are lazy so a visitor to the dashboard does not also download and
// parse the six views they did not open. Vite emits one chunk per import().
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./views/Dashboard.vue') },
    { path: '/inventory', component: () => import('./views/Inventory.vue') },
    { path: '/orders', component: () => import('./views/Orders.vue') },
    { path: '/demand', component: () => import('./views/Demand.vue') },
    { path: '/restocking', component: () => import('./views/Restocking.vue') },
    { path: '/spending', component: () => import('./views/Spending.vue') },
    { path: '/reports', component: () => import('./views/Reports.vue') }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
