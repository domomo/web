<script setup>
import { ref } from 'vue';
import { onBeforeRouteLeave, RouterLink, useRouter } from 'vue-router';
import { api } from '../api';

const router = useRouter();
const title = ref('');
const contents = ref('');
const pending = ref(false);
const error = ref('');
const errorElement = ref(null);

onBeforeRouteLeave(() => {
  if (pending.value || (!title.value && !contents.value)) return true;
  return window.confirm('작성 중인 노트가 있어요. 저장하지 않고 이동할까요?');
});

async function submit() {
  pending.value = true;
  error.value = '';
  try {
    const post = await api.createNote({ title: title.value.trim(), contents: contents.value.trim() });
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
    <div class="page-heading">
      <p class="page-kicker">오늘 남기는 기록</p>
      <h1 id="write-title">새 노트</h1>
      <p class="page-intro">잘 쓰려고 애쓰지 않아도 괜찮아요.</p>
    </div>
    <form class="page-panel writing-panel page-form" @submit.prevent="submit" :aria-busy="pending">
      <label for="post-title">제목</label>
      <input id="post-title" v-model="title" name="title" autocomplete="off" maxlength="200" placeholder="오늘은 어떤 하루였나요…" required />
      <label for="post-contents">내용</label>
      <textarea id="post-contents" v-model="contents" name="contents" autocomplete="off" spellcheck="false" placeholder="기억하고 싶은 순간을 적어보세요…" rows="12" required></textarea>
      <p v-if="error" ref="errorElement" class="inline-error" role="alert" tabindex="-1">{{ error }}</p>
      <div class="form-actions">
        <RouterLink class="quiet-link" :to="{ name: 'post-list' }">목록으로</RouterLink>
        <button class="button button-primary form-submit" type="submit" :disabled="pending">{{ pending ? '저장 중…' : '노트 저장' }}</button>
      </div>
    </form>
  </section>
</template>
