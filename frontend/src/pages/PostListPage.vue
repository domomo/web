<script setup>
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { api } from '../api';
import { postLoginNotice } from '../navigationNotice';

const route = useRoute();
const posts = ref([]);
const offset = ref(0);
const loading = ref(true);
const loadingMore = ref(false);
const hasMore = ref(true);
const error = ref('');
const signedIn = ref(postLoginNotice.value);
const registeredName = computed(() => route.query.registered === '1');

async function loadPosts(reset = false) {
  if (loadingMore.value || (loading.value && !reset)) return;
  if (reset) {
    loading.value = true;
    offset.value = 0;
    hasMore.value = true;
  } else {
    loadingMore.value = true;
  }
  error.value = '';
  try {
    const result = await api.listNotes(offset.value, 20);
    posts.value = reset ? result : [...posts.value, ...result];
    offset.value += result.length;
    hasMore.value = result.length === 20;
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '연결을 확인한 뒤 다시 시도해 주세요.';
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

onMounted(() => {
  postLoginNotice.value = false;
  loadPosts(true);
});
</script>

<template>
  <section class="posts-page" aria-labelledby="posts-title">
    <div class="page-heading list-page-heading">
      <div><p class="page-kicker">생각이 쌓이는 곳</p><h1 id="posts-title">노트 모아보기</h1><p class="page-intro">최근 기록부터 천천히 살펴보세요.</p></div>
      <RouterLink class="button button-primary create-link" :to="{ name: 'post-create' }">새 노트 쓰기</RouterLink>
    </div>

    <p v-if="signedIn" class="success-banner" role="status" aria-live="polite">로그인했어요. 기록을 이어가 보세요.</p>
    <p v-if="registeredName" class="success-banner" role="status" aria-live="polite">회원가입이 완료됐어요. 로그인한 뒤 기록을 시작할 수 있어요.</p>

    <div v-if="loading" class="post-skeleton-list" role="status" aria-live="polite" aria-busy="true">
      <span class="sr-only">노트 목록을 불러오고 있어요…</span>
      <div v-for="item in 6" :key="item" class="post-skeleton-row" aria-hidden="true"><span class="skeleton skeleton-number"></span><span class="skeleton-copy"><span class="skeleton skeleton-title"></span><span class="skeleton skeleton-line"></span></span></div>
    </div>

    <div v-else-if="error && !posts.length" class="empty-panel error-panel" role="alert">
      <h2>목록을 불러오지 못했어요.</h2><p>연결 상태를 확인한 뒤 다시 시도해 주세요.</p>
      <button class="button button-soft" type="button" @click="loadPosts(true)">다시 불러오기</button>
    </div>
    <div v-else-if="!posts.length" class="empty-panel">
      <span class="empty-symbol" aria-hidden="true">✳</span><h2>아직 기록이 없어요.</h2><p>첫 번째 노트로 오늘을 남겨보세요.</p>
      <RouterLink class="button button-primary" :to="{ name: 'post-create' }">첫 노트 쓰기</RouterLink>
    </div>
    <div v-else class="post-list" aria-live="polite">
      <RouterLink v-for="post in posts" :key="post.idx" class="post-list-row" :to="{ name: 'post-detail', params: { idx: post.idx } }">
        <span class="post-number">No. {{ post.idx }}</span>
        <span class="post-copy"><strong>{{ post.title }}</strong><span>{{ post.contents }}</span></span>
        <span class="post-chevron" aria-hidden="true">↗</span>
      </RouterLink>
      <p v-if="error" class="inline-error list-inline-error" role="alert">다음 노트를 불러오지 못했어요. <button type="button" @click="loadPosts()">다시 시도</button></p>
      <div v-if="loadingMore" class="more-skeleton" role="status" aria-live="polite"><span class="sr-only">이전 노트를 불러오고 있어요…</span><span v-for="item in 2" :key="item" class="skeleton skeleton-line" aria-hidden="true"></span></div>
      <button v-if="hasMore && !loadingMore" class="more-button" type="button" @click="loadPosts()">이전 노트 더 보기</button>
    </div>
  </section>
</template>
