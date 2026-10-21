<script setup>
import { nextTick, ref, watch } from 'vue';
import BrandButton from './BrandButton.vue';
import BrandTextField from './BrandTextField.vue';

const props = defineProps({
  mode: { type: String, default: 'login', validator: (value) => ['login', 'signup'].includes(value) },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  titleId: { type: String, default: '' },
  fieldPrefix: { type: String, default: 'account' },
  mark: { type: String, default: 'Y' },
  successNotice: { type: String, default: '' },
});

const emit = defineEmits(['submit']);
const errorElement = ref(null);

watch(() => props.error, async (value) => {
  if (!value) return;
  await nextTick();
  errorElement.value?.focus();
});

function submit(event) {
  const formData = new FormData(event.currentTarget);
  emit('submit', Object.fromEntries(formData.entries()));
}

function focusError() {
  errorElement.value?.focus();
}

defineExpose({ focusError });
</script>

<template>
  <section class="account-panel" :aria-labelledby="titleId || `account-${mode}-title`">
    <div class="account-panel__heading">
      <span class="account-panel__mark" aria-hidden="true">{{ mark }}</span>
      <h1 :id="titleId || `account-${mode}-title`">{{ title || (mode === 'login' ? '로그인' : '회원가입') }}</h1>
      <p>{{ description || (mode === 'login' ? '계정에 로그인하고 서비스를 이어서 이용하세요.' : '간단한 정보 입력으로 계정을 만들 수 있어요.') }}</p>
    </div>
    <p v-if="successNotice" class="account-panel__success" role="status" aria-live="polite">{{ successNotice }}</p>
    <form class="account-panel__form page-form" :aria-busy="loading" @submit.prevent="submit">
      <BrandTextField v-if="mode === 'signup'" :id="`${fieldPrefix}-name`" label="이름" name="name" autocomplete="name" placeholder="이름을 입력해 주세요" required />
      <BrandTextField :id="`${fieldPrefix}-email`" label="이메일" name="email" type="email" autocomplete="email" placeholder="you@example.com" required />
      <BrandTextField :id="`${fieldPrefix}-password`" label="비밀번호" name="password" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" placeholder="비밀번호를 입력해 주세요" required />
      <p v-if="error" ref="errorElement" class="account-panel__error" role="alert" tabindex="-1">{{ error }}</p>
      <BrandButton type="submit" :disabled="loading">{{ loading ? '처리 중…' : mode === 'login' ? '로그인' : '계정 만들기' }}</BrandButton>
      <slot name="after-submit" />
    </form>
    <slot name="footer" />
  </section>
</template>

<style scoped>
.account-panel { width: min(440px, 100%); margin: 0 auto; padding: clamp(24px, 5vw, 42px); border: 1px solid #e8edf4; border-radius: 22px; background: #fff; }
.account-panel__heading { margin-bottom: 30px; text-align: center; }
.account-panel__mark { display: grid; width: 46px; height: 46px; margin: 0 auto 20px; place-items: center; border-radius: 15px; background: #0064FF; color: #fff; font-size: 23px; font-weight: 800; }
.account-panel h1 { margin: 0; color: #172333; font-size: 27px; letter-spacing: -.8px; }
.account-panel__heading p { margin: 10px 0 0; color: #778396; font-size: 14px; line-height: 1.65; }
.account-panel__form { display: grid; gap: 18px; }
.account-panel__form :deep(.brand-button) { width: 100%; margin-top: 4px; }
.account-panel__form :deep(.brand-field label) { margin: 0; }
.account-panel__error { margin: -4px 0; color: #c03939; font-size: 13px; }
.account-panel__error:focus { outline: 2px solid #c03939; outline-offset: 3px; }
.account-panel__success { margin: 0 0 20px; border-radius: 11px; background: #edf4ff; padding: 13px 15px; color: #164ea9; font-size: 13px; line-height: 1.65; }
</style>
