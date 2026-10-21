<script setup>
import { nextTick, ref } from 'vue';
import { onBeforeRouteLeave, RouterLink, useRouter } from 'vue-router';
import BrandButton from '../components/BrandButton.vue';
import BrandTextField from '../components/BrandTextField.vue';
import PageHeading from '../components/PageHeading.vue';
import SurfacePanel from '../components/SurfacePanel.vue';
import { api } from '../api/api';
import { postCategories } from '../stores/postCategories';

const router = useRouter();
const title = ref('');
const contents = ref('');
const category = ref('');
const saleMode = ref('free');
const salePrice = ref('');
const preview = ref('');
const pending = ref(false);
const error = ref('');
const errorElement = ref(null);

onBeforeRouteLeave(() => {
  if (pending.value || (!title.value && !contents.value)) return true;
  return window.confirm('작성 중인 노트가 있어요. 저장하지 않고 이동할까요?');
});

async function submit() {
  if (saleMode.value === 'paid' && (!Number.isInteger(Number(salePrice.value)) || Number(salePrice.value) <= 0 || !preview.value.trim())) {
    error.value = '유료 글은 1원 이상의 가격과 미리보기를 입력해 주세요.';
    await nextTick();
    errorElement.value?.focus();
    return;
  }
  pending.value = true;
  error.value = '';
  try {
    const payload = { title: title.value.trim(), contents: contents.value.trim(), category: category.value };
    if (saleMode.value === 'paid') Object.assign(payload, { sale_price: Number(salePrice.value), preview: preview.value.trim() });
    const post = await api.createNote(payload);
    await router.push({ name: 'post-detail', params: { idx: post.idx } });
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '내용을 확인한 뒤 다시 저장해 주세요.';
    await nextTick();
    errorElement.value?.focus();
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <section class="writing-layout" aria-labelledby="write-title">
    <PageHeading title-id="write-title" kicker="오늘 남기는 기록" title="새 노트" description="잘 쓰려고 애쓰지 않아도 괜찮아요." />
    <SurfacePanel as="form" class="page-panel writing-panel page-form" @submit.prevent="submit" :aria-busy="pending">
      <BrandTextField id="post-title" label="제목" name="title" :model-value="title" autocomplete="off" :maxlength="200" placeholder="오늘은 어떤 하루였나요…" required @update:model-value="title = $event" />
      <label for="post-category">분야</label>
      <select id="post-category" v-model="category" name="category" required>
        <option disabled value="">분야를 선택해 주세요</option>
        <option v-for="item in postCategories" :key="item" :value="item">{{ item }}</option>
      </select>
      <label for="post-contents">내용</label>
      <textarea id="post-contents" v-model="contents" name="contents" autocomplete="off" spellcheck="false" placeholder="기억하고 싶은 순간을 적어보세요…" rows="12" required></textarea>
      <fieldset class="sale-options">
        <legend>공개 방식</legend>
        <label><input v-model="saleMode" type="radio" name="sale-mode" value="free" /> 무료 글</label>
        <label><input v-model="saleMode" type="radio" name="sale-mode" value="paid" /> 유료 글</label>
      </fieldset>
      <template v-if="saleMode === 'paid'">
        <BrandTextField id="post-price" label="가격 (원)" name="sale_price" type="number" :model-value="salePrice" min="1" step="1" required @update:model-value="salePrice = $event" />
        <label for="post-preview">무료 미리보기</label>
        <textarea id="post-preview" v-model="preview" name="preview" rows="4" required placeholder="독자가 먼저 읽을 수 있는 내용을 적어주세요."></textarea>
      </template>
      <p v-if="error" ref="errorElement" class="inline-error" role="alert" tabindex="-1">{{ error }}</p>
      <div class="form-actions">
        <RouterLink class="quiet-link" :to="{ name: 'post-list' }">목록으로</RouterLink>
        <BrandButton class="form-submit" type="submit" :disabled="pending">{{ pending ? '저장 중…' : '노트 저장' }}</BrandButton>
      </div>
    </SurfacePanel>
  </section>
</template>

<style scoped>
:deep(.sale-options) { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; margin: 8px 0 4px; padding: 0; border: 0; }
:deep(.sale-options legend) { flex: 0 0 100%; width: auto; margin: 0; color: #333d4a; font-size: 13px; font-weight: 600; }
:deep(.sale-options label) { display: inline-flex; min-height: 44px; flex: 0 0 auto; align-items: center; gap: 9px; margin: 0; padding: 0 15px; border: 1px solid #e1e6ee; border-radius: 11px; background: #fff; color: #596575; font-size: 14px; cursor: pointer; }
:deep(.sale-options label:has(input:checked)) { border-color: #0064ff; background: #f2f6ff; color: #0052d4; }
:deep(.sale-options input[type="radio"]) { width: 17px; min-width: 17px; min-height: 17px; height: 17px; margin: 0; padding: 0; accent-color: #0064ff; }
</style>
