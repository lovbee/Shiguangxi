import '@/assets/main.css'

import { createApp } from 'vue'
import App from '@/App.vue'

// 导入路由
import router from '@/router'

// 引入全局状态管理 Pinia
import pinia from '@/stores'

const app = createApp(App)

// 应用路由
app.use(router)
// 应用 Pinia
app.use(pinia)

app.mount('#app')
