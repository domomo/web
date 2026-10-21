import { createApp } from 'vue';
import App from './components/App.vue';
import { router } from './router/index';
import './assets/style.css';
import './assets/design.css';

createApp(App).use(router).mount('#app');
