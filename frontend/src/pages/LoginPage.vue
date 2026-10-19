<script setup>
import { computed, nextTick, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import { api } from '../api';
import { postLoginNotice } from '../navigationNotice';

const route = useRoute();
const router = useRouter();
const email = ref('');
const password = ref('');
const pending = ref(false);
const error = ref('');
const errorElement = ref(null);
const registered = computed(() => route.query.registered === '1');

async function submit() {
  pending.value = true;
  error.value = '';
  try {
    const result = await api.login({ email: email.value, password: password.value });
    if (!result?.email) throw new Error('이메일 또는 비밀번호를 확인해 주세요.');
    postLoginNotice.value = true;
    await router.push({ name: 'post-list' });
  } catch (cause) {
    error.value = cause?.message === 'Internal Server Error'
      ? '이메일 또는 비밀번호를 확인해 주세요.'
      : cause instanceof Error ? cause.message : '입력 내용을 확인한 뒤 다시 시도해 주세요.';
    await nextTick();
    errorElement.value?.focus();
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <section class="auth-layout" aria-labelledby="login-title">
    <div class="auth-note"><span class="auth-mark" aria-hidden="true">Y</span><p>다시 돌아온 오늘을<br />기록해 보세요.</p></div>
    <div class="page-panel auth-panel">
      <p class="page-kicker">기록 이어가기</p>
      <h1 id="login-title">로그인</h1>
      <p class="page-intro">여백에 남긴 생각이 기다리고 있어요.</p>
      <p v-if="registered" class="success-banner" role="status" aria-live="polite">가입이 완료됐어요. 이제 로그인해 주세요.</p>
      <form class="page-form" @submit.prevent="submit" :aria-busy="pending">
        <label for="login-email">이메일</label>
        <input id="login-email" v-model="email" name="email" type="email" autocomplete="email" spellcheck="false" placeholder="you@example.com…" required />
        <label for="login-password">비밀번호</label>
        <input id="login-password" v-model="password" name="password" type="password" autocomplete="current-password" placeholder="비밀번호를 입력해 주세요…" required />
        <p v-if="error" ref="errorElement" class="inline-error" role="alert" tabindex="-1">{{ error }}</p>
        <button class="button button-primary form-submit" type="submit" :disabled="pending">{{ pending ? '로그인 중…' : '로그인' }}</button>
      </form>
      <p class="auth-switch">처음 오셨나요? <RouterLink :to="{ name: 'signup' }">회원가입</RouterLink></p>
    </div>
  </section>
</template>
