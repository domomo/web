<script setup>
import { computed, nextTick, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import AccountPanel from '../components/AccountPanel.vue';
import { api } from '../api/api';
import { postLoginNotice } from '../stores/navigationNotice';
import { getKakaoSdk } from '../api/kakao';
import { setCurrentUser } from '../stores/auth';

const route = useRoute();
const router = useRouter();
const pending = ref(false);
const error = ref('');
const accountPanel = ref(null);
const registered = computed(() => route.query.registered === '1');
const oauthMessage = computed(() => ({
  cancelled: '카카오 로그인을 취소했어요.',
  invalid_state: '로그인 요청이 만료됐어요. 다시 시도해 주세요.',
  provider_error: '카카오 로그인을 완료하지 못했어요. 다시 시도해 주세요.',
  profile_error: '카카오 프로필 정보를 확인할 수 없어요.',
  server_error: '로그인 처리 중 문제가 생겼어요. 다시 시도해 주세요.',
}[route.query.oauth_error] || ''));
const displayedError = computed(() => error.value || oauthMessage.value);

async function loginWithKakao() {
  pending.value = true;
  error.value = '';
  try {
    const { state, redirect_uri: redirectUri } = await api.getKakaoLoginState();
    const sdk = getKakaoSdk();
    sdk.Auth.authorize({ redirectUri, scope: 'profile_nickname', state });
  } catch {
    error.value = '카카오 로그인을 시작하지 못했어요. 잠시 후 다시 시도해 주세요.';
    await nextTick();
    accountPanel.value?.focusError();
  } finally {
    pending.value = false;
  }
}

async function submit({ email, password }) {
  pending.value = true;
  error.value = '';
  try {
    const result = await api.login({ email, password });
    if (!result?.email) throw new Error('이메일 또는 비밀번호를 확인해 주세요.');
    setCurrentUser(result);
    postLoginNotice.value = true;
    await router.push({ name: 'post-list' });
  } catch (cause) {
    error.value = cause?.message === 'Internal Server Error'
      ? '이메일 또는 비밀번호를 확인해 주세요.'
      : cause instanceof Error ? cause.message : '입력 내용을 확인한 뒤 다시 시도해 주세요.';
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <section class="auth-page" aria-labelledby="login-title">
    <AccountPanel
      ref="accountPanel"
      mode="login"
      field-prefix="login"
      title-id="login-title"
      title="로그인"
      description="여백에 남긴 생각이 기다리고 있어요."
      :loading="pending"
      :error="displayedError"
      :success-notice="registered ? '가입이 완료됐어요. 이제 로그인해 주세요.' : ''"
      @submit="submit"
    >
      <template #after-submit>
        <div class="auth-divider" aria-hidden="true"><span>또는</span></div>
        <button class="kakao-login-button" type="button" data-testid="kakao-login" :disabled="pending" @click="loginWithKakao">
          <span class="kakao-login-mark" aria-hidden="true">K</span>
          {{ pending ? '카카오 연결 중…' : '카카오로 로그인' }}
        </button>
      </template>
      <template #footer>
        <p class="auth-switch">처음 오셨나요? <RouterLink :to="{ name: 'signup' }">회원가입</RouterLink></p>
      </template>
    </AccountPanel>
  </section>
</template>

<style scoped>
.auth-page { max-width: 520px; margin: 52px auto 68px; padding: 0 20px; }
.auth-divider { display: flex; align-items: center; gap: 12px; color: #9298a2; font-size: 12px; }
.auth-divider::before, .auth-divider::after { height: 1px; flex: 1; background: #e9edf2; content: ''; }
.kakao-login-button { display: flex; width: 100%; min-height: 48px; align-items: center; justify-content: center; gap: 10px; border: 1px solid #f3d900; border-radius: 11px; background: #fee500; color: #191919; font-size: 14px; font-weight: 700; }
.kakao-login-button:focus-visible { outline: 3px solid #333; outline-offset: 3px; }
.kakao-login-mark { display: grid; width: 23px; height: 23px; place-items: center; border-radius: 50%; background: #191919; color: #fee500; font-size: 13px; font-weight: 700; }
.auth-switch { margin: 24px 0 0; color: #7b8794; font-size: 13px; text-align: center; }
.auth-switch a { color: #0064ff; font-weight: 700; text-underline-offset: 3px; }
</style>
