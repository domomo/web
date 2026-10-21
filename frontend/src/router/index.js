import { createRouter, createWebHistory } from 'vue-router';
import { ref } from 'vue';

export const navigationBusy = ref(false);

export const router = createRouter({
  history: createWebHistory('/'),
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 };
  },
  routes: [
    { path: '/', redirect: { name: 'post-list' } },
    { path: '/signup', name: 'signup', component: () => import('../views/SignupPage.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginPage.vue') },
    { path: '/posts', name: 'post-list', component: () => import('../views/PostListPage.vue') },
    { path: '/posts/new', name: 'post-create', component: () => import('../views/PostCreatePage.vue') },
    { path: '/posts/:idx(\\d+)', name: 'post-detail', component: () => import('../views/PostDetailPage.vue') },
    { path: '/:pathMatch(.*)*', redirect: { name: 'post-list' } },
  ],
});

router.beforeEach(() => {
  navigationBusy.value = true;
});

router.afterEach(() => {
  navigationBusy.value = false;
});

router.onError(() => {
  navigationBusy.value = false;
});
