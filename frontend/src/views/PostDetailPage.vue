<script setup>
import { onMounted, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import BrandButton from '../components/BrandButton.vue';
import PageHeading from '../components/PageHeading.vue';
import ProductDetail from '../components/ProductDetail.vue';
import SurfacePanel from '../components/SurfacePanel.vue';
import { api } from '../api/api';
import { requestArticlePayment } from '../api/portone';

const route = useRoute();
const post = ref(null);
const loading = ref(true);
const error = ref('');
const purchasePending = ref(false);
const purchaseError = ref('');
const purchaseStatus = ref(null);
const paymentConfig = ref(null);

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

onMounted(async () => {
  await loadPost();
  try {
    paymentConfig.value = await api.getPaymentConfig();
  } catch {
    paymentConfig.value = { configured: false };
  }
  if (route.query.code) {
    purchaseError.value = String(route.query.message || '결제가 완료되지 않았어요. 다시 시도해 주세요.');
  } else if (route.query.paymentId) {
    await confirmPayment(route.query.paymentId);
  }
});

async function confirmPayment(paymentId) {
  purchasePending.value = true;
  purchaseError.value = '';
  try {
    await api.confirmPurchase(paymentId);
    await loadPost();
  } catch (cause) {
    purchaseError.value = cause instanceof Error ? cause.message : '결제 확인에 실패했어요.';
    purchaseStatus.value = cause?.status ?? null;
  } finally {
    purchasePending.value = false;
  }
}

function paymentReturnUrl(paymentId) {
  const url = new URL(window.location.href);
  url.searchParams.set('paymentId', paymentId);
  return url.toString();
}

async function purchase() {
  purchasePending.value = true;
  purchaseError.value = '';
  purchaseStatus.value = null;
  try {
    if (!paymentConfig.value?.configured) throw new Error('포트원 토스페이먼츠 결제 설정이 준비되지 않았어요.');
    const paymentId = await requestArticlePayment(api, route.params.idx, paymentConfig.value, paymentReturnUrl);
    await confirmPayment(paymentId);
  } catch (cause) {
    purchaseError.value = cause instanceof Error ? cause.message : '구매를 완료하지 못했어요.';
    purchaseStatus.value = cause?.status ?? null;
  } finally {
    purchasePending.value = false;
  }
}
</script>

<template>
  <section class="detail-page" aria-labelledby="detail-title" :aria-busy="loading">
    <PageHeading title-id="detail-title" kicker="기록 다시 읽기" title="노트 상세">
      <template #trailing><RouterLink class="quiet-link" :to="{ name: 'post-list' }">← 목록으로</RouterLink></template>
    </PageHeading>

    <SurfacePanel v-if="loading" as="article" class="page-panel detail-skeleton" role="status" aria-live="polite" aria-busy="true">
      <span class="sr-only">노트를 불러오고 있어요…</span>
      <div class="skeleton skeleton-number" aria-hidden="true"></div><div class="skeleton skeleton-title" aria-hidden="true"></div>
      <div class="skeleton-paragraph" aria-hidden="true"><span v-for="line in 5" :key="line" class="skeleton skeleton-line"></span></div>
    </SurfacePanel>
    <SurfacePanel v-else-if="error" as="div" tone="soft" class="empty-panel error-panel" role="alert">
      <h2>노트를 열지 못했어요.</h2><p>{{ error }}</p>
      <BrandButton :to="{ name: 'post-list' }" variant="secondary">목록으로 돌아가기</BrandButton>
    </SurfacePanel>
    <ProductDetail
      v-else
      :eyebrow="post.category || '분야 미지정'"
      :title="post.title"
      :show-action="post.contents == null && !post.is_author && !post.has_purchased"
      :action-disabled="purchasePending || !paymentConfig?.configured"
      :action-label="purchasePending ? '구매 중…' : '이 글 구매하기'"
    >
      <template #content>
        <div class="detail-copy">
          <p class="post-number">NOTE No. {{ post.idx }}</p>
          <p v-if="post.is_for_sale" class="sale-summary"><span>{{ Number(post.sale_price).toLocaleString('ko-KR') }}원</span><span v-if="post.author_name">작성자 {{ post.author_name }}</span></p>
          <p class="detail-content">{{ post.contents ?? post.preview }}</p>
          <p v-if="post.contents == null" class="locked-note">전문은 구매 후 읽을 수 있어요.</p>
          <p v-if="post.contents == null && !paymentConfig?.configured" class="payment-config-note">결제 설정이 준비되면 구매할 수 있어요.</p>
          <RouterLink v-if="post.contents == null && !post.is_author && !post.has_purchased && purchaseStatus === 401" class="quiet-link" :to="{ name: 'login' }">로그인하기</RouterLink>
          <p v-if="purchaseError" class="inline-error" role="alert">{{ purchaseError }}</p>
        </div>
      </template>
      <template #visual>
        <div class="detail-art" aria-hidden="true"><span>여백</span><strong>오늘의 기록</strong><i>✳</i></div>
      </template>
      <template #action>
        <BrandButton v-if="post.contents == null && !post.is_author && !post.has_purchased" data-testid="purchase-note" :disabled="purchasePending || !paymentConfig?.configured" @click="purchase">{{ purchasePending ? '구매 중…' : '이 글 구매하기' }}</BrandButton>
        <BrandButton v-else :to="{ name: 'post-create' }">새 노트 쓰기</BrandButton>
      </template>
    </ProductDetail>
  </section>
</template>

<style scoped>
.sale-summary { display: flex; gap: 14px; margin: 0 0 22px; color: #0064ff; font-size: 13px; font-weight: 700; }
.detail-copy { margin-top: 18px; }
.detail-copy .post-number { margin: 0 0 14px; color: #8b95a1; font-size: 12px; }
.detail-content { margin: 0; padding: 22px; border-radius: 14px; background: #f7f9fc; color: #3e4855; font-size: 15px; line-height: 2; white-space: pre-wrap; overflow-wrap: anywhere; }
.locked-note { margin: 16px 0 0; color: #6b7684; font-size: 13px; }
.payment-config-note { color: #778396; font-size: 13px; }
.detail-art { display: flex; min-height: 260px; flex-direction: column; align-items: flex-start; justify-content: space-between; padding: 30px; border: 1px solid #d9e6ff; border-radius: 22px; background: linear-gradient(145deg, #eef5ff, #dceaff); color: #0064ff; }
.detail-art span { font-size: 13px; font-weight: 750; }
.detail-art strong { align-self: flex-end; color: #26364b; font-size: 22px; letter-spacing: -1px; }
.detail-art i { align-self: flex-end; color: #79a8ff; font-size: 48px; font-style: normal; }
@media(max-width:700px) { .detail-art { min-height: 180px; } }
</style>
