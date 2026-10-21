<script setup>
import { RouterLink } from 'vue-router';
defineProps({
  brand: { type: String, default: '여백' },
  navItems: { type: Array, required: true },
  loginTo: { type: [String, Object], required: true },
  signupTo: { type: [String, Object], required: true },
  user: { type: Object, default: null },
  logoutPending: { type: Boolean, default: false },
  logoutError: { type: String, default: '' },
});
defineEmits(['logout']);
</script>

<template>
  <header class="topbar">
    <RouterLink class="brand" :to="navItems[0]?.to || '/'" :aria-label="`${brand} 홈`">
      <span class="brand-mark" aria-hidden="true">Y</span>
      <span class="brand-copy">{{ brand }}</span>
    </RouterLink>
    <nav class="main-nav" aria-label="주요 메뉴">
      <RouterLink v-for="item in navItems" :key="item.label" :to="item.to">{{ item.label }}</RouterLink>
    </nav>
    <div class="account-nav">
      <template v-if="user">
        <span class="profile" data-testid="user-profile" :title="user.email || user.name">
          <span class="profile-mark" aria-hidden="true">{{ user.name?.slice(0, 1) || '나' }}</span>
          <span>{{ user.name }}님</span>
        </span>
        <button class="logout-button" type="button" :disabled="logoutPending" @click="$emit('logout')">
          {{ logoutPending ? '로그아웃 중…' : '로그아웃' }}
        </button>
      </template>
      <template v-else>
        <RouterLink :to="loginTo">로그인</RouterLink>
        <RouterLink class="signup-link" :to="signupTo">회원가입</RouterLink>
      </template>
    </div>
    <p v-if="logoutError" class="logout-error" role="alert" aria-live="assertive">{{ logoutError }}</p>
  </header>
</template>

<style scoped>
.topbar { position: sticky; z-index: 5; top: 0; display: flex; min-height: 72px; align-items: center; gap: clamp(20px, 4vw, 58px); padding: 0 max(36px, calc((100vw - 1120px) / 2)); border-bottom: 1px solid #edf0f4; background: rgb(255 255 255 / 94%); backdrop-filter: blur(14px); }
.brand { display: inline-flex; flex: none; align-items: center; gap: 9px; color: #202a38; font-size: 18px; font-weight: 800; letter-spacing: -.5px; text-decoration: none; }
.brand-mark { display: grid; width: 32px; height: 32px; place-items: center; border-radius: 11px; background: #0064FF; color: #fff; font-size: 16px; }
.brand-copy { color: #191f28; font-size: 18px; letter-spacing: -.8px; }
.main-nav, .account-nav { display: flex; align-items: center; gap: 8px; }
.main-nav { margin-left: auto; }
.main-nav a, .account-nav a, .logout-button { display: inline-flex; min-height: 40px; align-items: center; padding: 0 13px; border: 0; border-radius: 10px; background: transparent; color: #697587; font: inherit; font-size: 14px; font-weight: 650; text-decoration: none; cursor: pointer; }
.main-nav a:hover, .main-nav a.router-link-active, .account-nav a:hover { background: #f1f6ff; color: #0064FF; }
.logout-button:hover:not(:disabled) { background: #f1f6ff; color: #0064FF; }
.logout-button:focus-visible { outline: 3px solid #0064ff; outline-offset: 2px; }
.logout-button:disabled { cursor: wait; opacity: .65; }
.logout-error { position: absolute; top: calc(100% + 4px); right: max(36px, calc((100vw - 1120px) / 2)); margin: 0; padding: 8px 12px; border: 1px solid #f0b8b8; border-radius: 8px; background: #fff7f7; color: #a12626; font-size: 13px; }
.account-nav .signup-link { background: #0064FF; color: #fff; }
.account-nav .signup-link:hover { background: #0052d4; color: #fff; }
.account-nav .profile { display: inline-flex; min-height: 40px; align-items: center; gap: 8px; padding: 0 11px; color: #303b4a; font-size: 14px; font-weight: 650; }
.profile-mark { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 50%; background: #eaf1ff; color: #0064ff; font-size: 13px; }
@media (max-width: 760px) { .topbar { padding: 0 24px; } }
@media (max-width: 560px) { .topbar { min-height: 68px; flex-wrap: wrap; gap: 8px 14px; padding: 10px 18px; } .main-nav { margin: 0 auto 0 0; } .main-nav a, .account-nav a { padding: 0 9px; font-size: 12px; } .account-nav { gap: 2px; } }
</style>
