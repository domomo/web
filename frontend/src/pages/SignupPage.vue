<script setup>
import { nextTick, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import { api } from '../api';

const router = useRouter();
const email = ref('');
const name = ref('');
const password = ref('');
const pending = ref(false);
const error = ref('');
const errorElement = ref(null);

async function submit() {
  pending.value = true;
  error.value = '';
  try {
    await api.signUp({ email: email.value, name: name.value, password: password.value });
    await router.push({ name: 'login', query: { registered: '1' } });
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '입력 내용을 확인한 뒤 다시 시도해 주세요.';
    await nextTick();
    errorElement.value?.focus();
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <section class="auth-layout" aria-labelledby="signup-title">
    <div class="auth-note"><span class="auth-mark" aria-hidden="true">Y</span><p>나만의 기록 공간을<br />천천히 시작해 보세요.</p></div>
    <div class="page-panel auth-panel">
      <p class="page-kicker">새로운 시작</p>
      <h1 id="signup-title">여백 만들기</h1>
      <p class="page-intro">기록을 보관할 계정을 만들어요.</p>
      <form class="page-form" @submit.prevent="submit" :aria-busy="pending">
        <label for="signup-name">이름</label>
        <input id="signup-name" v-model="name" name="name" autocomplete="name" placeholder="이름을 입력해 주세요…" required />
        <label for="signup-email">이메일</label>
        <input id="signup-email" v-model="email" name="email" type="email" autocomplete="email" spellcheck="false" placeholder="you@example.com…" required />
        <label for="signup-password">비밀번호</label>
        <input id="signup-password" v-model="password" name="password" type="password" autocomplete="new-password" placeholder="비밀번호를 입력해 주세요…" required />
        <p v-if="error" ref="errorElement" class="inline-error" role="alert" tabindex="-1">{{ error }}</p>
        <button class="button button-primary form-submit" type="submit" :disabled="pending">{{ pending ? '계정을 만들고 있어요…' : '회원가입' }}</button>
      </form>
      <p class="auth-switch">이미 계정이 있나요? <RouterLink :to="{ name: 'login' }">로그인</RouterLink></p>
    </div>
  </section>
</template>
