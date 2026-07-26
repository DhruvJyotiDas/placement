import { createApp } from 'vue'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './styles.css'

import App from './App.vue'
import router from './router/index.js'

createApp(App).use(router).mount('#app')
