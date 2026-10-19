<script setup>
import { onMounted, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { api } from '../api';

const route = useRoute();
const post = ref(null);
const loading = ref(true);
const error = ref('');

async function loadPost() {
  loading.value = true;
  error.value = '';
  try {
    const result = await api.getNote(route.params.idx);
    if (!result || typeof result.idx !== 'number') throw new Error('해당 번호의 노트를 찾지 못했어요. 번호를 확인해 주세요.');
    post.value = result;
  } catch (cause) {
    post.value = null;
    error.value = cause instanceof Error ? cause.message : '노트 번호를 확인한 뒤 다시 시도해 주세요.';
  } finally {
    loading.value = false;
  }
}

onMounted(loadPost);
</script>

<template>
  <section class="detail-page" aria-labelledby="detail-title" :aria-busy="loading">
    <div class="page-heading detail-page-heading">
      <div><p class="page-kicker">기록 다시 읽기</p><h1 id="detail-title">노트 상세</h1></div>
      <RouterLink class="quiet-link" :to="{ name: 'post-list' }">← 목록으로</RouterLink>
    </div>

    <article v-if="loading" class="page-panel detail-skeleton" role="status" aria-live="polite" aria-busy="true">
      <span class="sr-only">노트를 불러오고 있어요…</span>
      <div class="skeleton skeleton-number" aria-hidden="true"></div><div class="skeleton skeleton-title" aria-hidden="true"></div>
      <div class="skeleton-paragraph" aria-hidden="true"><span v-for="line in 5" :key="line" class="skeleton skeleton-line"></span></div>
    </article>
    <div v-else-if="error" class="empty-panel error-panel" role="alert">
      <h2>노트를 열지 못했어요.</h2><p>{{ error }}</p>
      <RouterLink class="button button-soft" :to="{ name: 'post-list' }">목록으로 돌아가기</RouterLink>
    </div>
    <article v-else class="page-panel detail-panel">
      <p class="post-number">NOTE No. {{ post.idx }}</p>
      <h2>{{ post.title }}</h2>
      <p class="detail-content">{{ post.contents }}</p>
      <div class="detail-actions"><RouterLink class="quiet-link" :to="{ name: 'post-list' }">목록으로</RouterLink><RouterLink class="button button-primary" :to="{ name: 'post-create' }">새 노트 쓰기</RouterLink></div>
    </article>
  </section>
</template>
