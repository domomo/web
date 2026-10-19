<script setup>
import { RouterLink, RouterView } from 'vue-router';
import { navigationBusy } from './router';
</script>

<template>
  <div class="site-shell">
    <a class="skip-link" href="#main-content">본문으로 건너뛰기</a>
    <header class="topbar">
      <RouterLink class="brand" :to="{ name: 'post-list' }" aria-label="여백 홈">
        <span class="brand-mark" aria-hidden="true">Y</span>
        <span class="brand-copy">여백<span>NOTE SPACE</span></span>
      </RouterLink>
      <nav class="main-nav" aria-label="주요 메뉴">
        <RouterLink :to="{ name: 'post-list' }">노트 목록</RouterLink>
        <RouterLink :to="{ name: 'post-create' }">새 노트</RouterLink>
      </nav>
      <div class="account-nav">
        <RouterLink :to="{ name: 'login' }">로그인</RouterLink>
        <RouterLink class="signup-link" :to="{ name: 'signup' }">회원가입</RouterLink>
      </div>
    </header>

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
