<script setup>
import { onMounted, ref } from 'vue';
import { RouterLink, RouterView } from 'vue-router';
import { navigationBusy } from '../router/index';
import { api } from '../api/api';
import { authRevision, currentUser, setCurrentUser } from '../stores/auth';
import ServiceHeader from './ServiceHeader.vue';

const logoutPending = ref(false);
const logoutError = ref('');

async function logout() {
  logoutPending.value = true;
  logoutError.value = '';
  try {
    await api.logout();
    setCurrentUser(null);
  } catch {
    logoutError.value = '로그아웃하지 못했어요. 잠시 후 다시 시도해 주세요.';
  } finally {
    logoutPending.value = false;
  }
}

onMounted(async () => {
  const revision = authRevision.value;
  try {
    const user = await api.getCurrentUser();
    if (authRevision.value === revision) setCurrentUser(user);
  } catch {
    if (authRevision.value === revision) setCurrentUser(null);
  }
});
</script>

<template>
  <div class="site-shell">
    <a class="skip-link" href="#main-content">본문으로 건너뛰기</a>
    <ServiceHeader
      :nav-items="[
        { label: '노트', to: { name: 'post-list' } },
        { label: '기록하기', to: { name: 'post-create' } },
      ]"
      :login-to="{ name: 'login' }"
      :signup-to="{ name: 'signup' }"
      :user="currentUser"
      :logout-pending="logoutPending"
      :logout-error="logoutError"
      @logout="logout"
    />

    <div v-if="navigationBusy" class="route-progress" role="status" aria-live="polite">
      <span class="sr-only">화면을 여는 중…</span>
    </div>
    <main id="main-content" tabindex="-1">
      <RouterView v-slot="{ Component, route }">
        <Transition name="page" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </RouterView>
    </main>

    <footer class="footer"><span>여백 <i aria-hidden="true">·</i> 생각을 위한 작은 공간</span><span>천천히, 오래.</span></footer>
  </div>
</template>

<style scoped>
.site-shell { max-width: none; padding: 0; }
.footer { max-width: 1120px; margin: 0 auto; border-top: 1px solid #edf0f2; }
</style>
