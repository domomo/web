<script setup>
import { ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import AccountPanel from '../components/AccountPanel.vue';
import { api } from '../api/api';

const router = useRouter();
const pending = ref(false);
const error = ref('');

async function submit({ email, name, password }) {
  pending.value = true;
  error.value = '';
  try {
    await api.signUp({ email, name, password });
    await router.push({ name: 'login', query: { registered: '1' } });
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '입력 내용을 확인한 뒤 다시 시도해 주세요.';
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <section class="auth-page" aria-labelledby="signup-title">
    <AccountPanel
      mode="signup"
      field-prefix="signup"
      title-id="signup-title"
      title="여백 만들기"
      description="기록을 보관할 계정을 만들어요."
      :loading="pending"
      :error="error"
      @submit="submit"
    >
      <template #footer>
        <p class="auth-switch">이미 계정이 있나요? <RouterLink :to="{ name: 'login' }">로그인</RouterLink></p>
      </template>
    </AccountPanel>
  </section>
</template>

<style scoped>
.auth-page { max-width: 520px; margin: 52px auto 68px; padding: 0 20px; }
.auth-switch { margin: 24px 0 0; color: #7b8794; font-size: 13px; text-align: center; }
.auth-switch a { color: #0064ff; font-weight: 700; text-underline-offset: 3px; }
</style>
