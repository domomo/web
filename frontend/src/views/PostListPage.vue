<script setup>
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import BrandButton from '../components/BrandButton.vue';
import PageHeading from '../components/PageHeading.vue';
import ServiceCard from '../components/ServiceCard.vue';
import ServiceTabs from '../components/ServiceTabs.vue';
import { api } from '../api/api';
import { postLoginNotice } from '../stores/navigationNotice';
import { postCategories } from '../stores/postCategories';
import { requestArticlePayment } from '../api/portone';

const route = useRoute();
const router = useRouter();
const posts = ref([]);
const offset = ref(0);
const loading = ref(true);
const loadingMore = ref(false);
const hasMore = ref(true);
const error = ref('');
const signedIn = ref(postLoginNotice.value);
const registeredName = computed(() => route.query.registered === '1');
const activeCategory = ref('');
const activeSaleType = ref('');
const paymentConfig = ref(null);
const purchasePending = ref(null);
const purchaseError = ref('');
let requestVersion = 0;

async function loadPosts(reset = false) {
  if (!reset && (loadingMore.value || loading.value)) return;
  const version = ++requestVersion;
  const requestedCategory = activeCategory.value;
  if (reset) {
    loading.value = true;
    loadingMore.value = false;
    offset.value = 0;
    hasMore.value = true;
    posts.value = [];
  } else {
    loadingMore.value = true;
  }
  error.value = '';
  try {
    const result = activeSaleType.value
      ? await api.listNotes(offset.value, 20, requestedCategory || undefined, activeSaleType.value)
      : requestedCategory
        ? await api.listNotes(offset.value, 20, requestedCategory)
        : await api.listNotes(offset.value, 20);
    if (version !== requestVersion) return;
    posts.value = reset ? result : [...posts.value, ...result];
    offset.value += result.length;
    hasMore.value = result.length === 20;
  } catch (cause) {
    if (version !== requestVersion) return;
    error.value = cause instanceof Error ? cause.message : '연결을 확인한 뒤 다시 시도해 주세요.';
  } finally {
    if (version === requestVersion) {
      loading.value = false;
      loadingMore.value = false;
    }
  }
}

function selectCategory(category) {
  if (activeCategory.value === category) return;
  activeCategory.value = category;
  loadPosts(true);
}

function selectSaleType(saleType) {
  if (activeSaleType.value === saleType) return;
  activeSaleType.value = saleType;
  loadPosts(true);
}

function paymentReturnUrl(paymentId) {
  const url = new URL(window.location.href);
  url.searchParams.set('paymentId', paymentId);
  return url.toString();
}

async function handleReturnedPayment(paymentId) {
  purchasePending.value = 'returning';
  try {
    const purchase = await api.confirmPurchase(paymentId);
    await router.replace({ name: 'post-detail', params: { idx: purchase.board_idx } });
  } catch (cause) {
    purchaseError.value = cause instanceof Error ? cause.message : '결제를 확인하지 못했어요.';
  } finally {
    purchasePending.value = null;
  }
}

async function buyPost(post) {
  if (!paymentConfig.value?.configured) {
    purchaseError.value = '포트원 결제 설정이 준비되지 않았어요.';
    return;
  }
  purchasePending.value = post.idx;
  purchaseError.value = '';
  try {
    const paymentId = await requestArticlePayment(api, post.idx, paymentConfig.value, paymentReturnUrl);
    const purchase = await api.confirmPurchase(paymentId);
    await router.push({ name: 'post-detail', params: { idx: purchase.board_idx } });
  } catch (cause) {
    purchaseError.value = cause instanceof Error ? cause.message : '구매를 완료하지 못했어요.';
  } finally {
    purchasePending.value = null;
  }
}

onMounted(async () => {
  postLoginNotice.value = false;
  try {
    paymentConfig.value = await api.getPaymentConfig();
  } catch {
    paymentConfig.value = { configured: false };
  }
  await loadPosts(true);
  if (route.query.code) purchaseError.value = String(route.query.message || '결제가 완료되지 않았어요. 다시 시도해 주세요.');
  else if (route.query.paymentId) await handleReturnedPayment(route.query.paymentId);
});
</script>

<template>
  <section class="posts-page" aria-labelledby="posts-title">
    <div class="list-hero">
      <div class="hero-copy">
        <p class="page-kicker">생각을 정리하는 가장 쉬운 방법</p>
        <h1 id="posts-title">기록은 가볍게,<br />찾기는 쉽게</h1>
        <p class="page-intro">떠오른 생각을 남기고, 다시 꺼내 볼 수 있어요.</p>
        <BrandButton class="create-link" :to="{ name: 'post-create' }">첫 기록 남기기 <span aria-hidden="true">↗</span></BrandButton>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div>
        <div class="note note-back"><span></span><span></span><span></span></div>
        <div class="note note-front"><i>✳</i><b>오늘의 기록</b><span></span><span></span><span></span></div>
        <span class="art-spark spark-one">✦</span><span class="art-spark spark-two">✳</span>
      </div>
    </div>

    <p v-if="signedIn" class="success-banner" role="status" aria-live="polite">로그인했어요. 기록을 이어가 보세요.</p>
    <p v-if="registeredName" class="success-banner" role="status" aria-live="polite">회원가입이 완료됐어요. 로그인한 뒤 기록을 시작할 수 있어요.</p>

    <PageHeading class="list-toolbar" title-tag="h2" variant="section" :title="activeCategory || '분야별 기록'" description="생각과 순간을 한곳에서 살펴보세요.">
      <template #trailing><span class="sort-label"><span class="sort-dot"></span> 최근 작성순</span></template>
    </PageHeading>

    <ServiceTabs class="category-tabs" variant="pills" label="분야별 노트" :tabs="[{ label: '종합', value: '' }, ...postCategories.map((category) => ({ label: category, value: category }))]" :model-value="activeCategory" @change="selectCategory" />

    <ServiceTabs class="sale-tabs" variant="segmented" label="무료·유료 글" :tabs="[{ label: '전체 글', value: '' }, { label: '무료', value: 'free' }, { label: '유료', value: 'paid' }]" :model-value="activeSaleType" @change="selectSaleType" />

    <div v-if="loading" class="post-skeleton-list" role="status" aria-live="polite" aria-busy="true">
      <span class="sr-only">노트 목록을 불러오고 있어요…</span>
      <div v-for="item in 6" :key="item" class="post-skeleton-row" aria-hidden="true"><span class="skeleton skeleton-number"></span><span class="skeleton-copy"><span class="skeleton skeleton-title"></span><span class="skeleton skeleton-line"></span></span></div>
    </div>

    <div v-else-if="error && !posts.length" class="empty-panel error-panel" role="alert">
      <h2>목록을 불러오지 못했어요.</h2><p>연결 상태를 확인한 뒤 다시 시도해 주세요.</p>
      <BrandButton variant="secondary" @click="loadPosts(true)">다시 불러오기</BrandButton>
    </div>
    <div v-else-if="!posts.length" class="empty-panel">
      <span class="empty-symbol" aria-hidden="true">✳</span><h2>아직 기록이 없어요.</h2><p>첫 번째 노트로 오늘을 남겨보세요.</p>
      <BrandButton :to="{ name: 'post-create' }">첫 노트 쓰기</BrandButton>
    </div>
    <div v-else class="post-card-grid" aria-live="polite">
      <ServiceCard
        v-for="(post, index) in posts"
        :key="post.idx"
        :title="post.title"
        :description="(post.is_for_sale ? post.preview : post.contents) || '기록을 열어 자세히 읽어보세요.'"
        :category="post.category || `노트 ${String(post.idx).padStart(2, '0')}`"
        :icon="['✳', '◒', '⌁', '✦'][index % 4]"
        :to="{ name: 'post-detail', params: { idx: post.idx } }"
        action-label="노트 읽기"
      >
        <template #action>
          <BrandButton v-if="post.is_for_sale && !post.is_author && !post.has_purchased" class="list-purchase-button" :disabled="purchasePending === post.idx || !paymentConfig?.configured" :aria-label="`${post.title} 구매하기`" @click="buyPost(post)">{{ purchasePending === post.idx ? '결제 중…' : '구매하기' }}</BrandButton>
          <span v-else-if="post.is_for_sale && post.has_purchased" class="purchased-label">구매 완료</span>
          <span v-if="post.is_for_sale" class="post-price">{{ Number(post.sale_price).toLocaleString('ko-KR') }}원</span>
        </template>
      </ServiceCard>
      <p v-if="purchaseError" class="inline-error" role="alert">{{ purchaseError }}</p>
      <p v-if="error" class="inline-error list-inline-error" role="alert">다음 노트를 불러오지 못했어요. <button type="button" @click="loadPosts()">다시 시도</button></p>
      <div v-if="loadingMore" class="more-skeleton" role="status" aria-live="polite"><span class="sr-only">이전 노트를 불러오고 있어요…</span><span v-for="item in 2" :key="item" class="skeleton skeleton-line" aria-hidden="true"></span></div>
      <BrandButton v-if="hasMore && !loadingMore" class="more-button" variant="secondary" @click="loadPosts()">이전 노트 더 보기</BrandButton>
    </div>
  </section>
</template>

<style scoped>
.posts-page { max-width: 1120px; padding: 0 0 80px; color: #191f28; }
.post-card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.post-card-grid :deep(.service-card) { min-height: 280px; }
.post-card-grid :deep(.service-card > .brand-button) { width: 100%; }
.post-card-grid :deep(.service-card__top) { min-height: 48px; }
.list-purchase-button { width: 100%; margin-top: 10px; }
.post-price { display: block; margin-top: 10px; color: #0064ff; font-size: 13px; font-weight: 750; }
.purchased-label { display: inline-block; margin-top: 10px; color: #168566; font-size: 12px; font-weight: 700; }
.list-hero { position: relative; display: flex; min-height: 384px; align-items: center; justify-content: space-between; overflow: hidden; margin: 36px 0 0; padding: 54px 8.3%; border-radius: 24px; background: #f4f7ff; }
.hero-copy { position: relative; z-index: 1; }
.page-kicker { margin: 0 0 20px; color: #4c78d8; font-size: 14px; font-weight: 600; letter-spacing: -.2px; }
.page-heading h1, .list-hero h1 { margin: 0; color: #191f28; font-size: clamp(38px, 5vw, 58px); font-weight: 750; line-height: 1.3; letter-spacing: -2.8px; }
.page-intro { margin: 17px 0 27px; color: #6b7684; font-size: 16px; line-height: 1.8; }
.create-link { min-height: 50px; gap: 24px; padding: 0 20px; border-radius: 12px; font-size: 14px; text-decoration: none; box-shadow: 0 6px 14px #0064ff24; }
.create-link span { font-size: 17px; }
.hero-art { position: relative; width: 330px; height: 260px; flex: none; overflow: visible; border-radius: 0; background: transparent; }
.orbit { position: absolute; top: 21px; left: 18px; width: 250px; height: 210px; border: 1px solid #dce6ff; border-radius: 50%; transform: rotate(-22deg); }
.orbit-two { top: 35px; left: 54px; width: 222px; height: 182px; transform: rotate(32deg); }
.note { position: absolute; display: grid; align-content: center; gap: 13px; width: 170px; height: 205px; padding: 28px; border-radius: 20px; box-shadow: 0 22px 50px #4a69a324; }
.note span { display: block; width: 100%; height: 6px; border-radius: 5px; background: #e9edf4; }
.note span:nth-last-child(1) { width: 62%; }
.note-back { top: 31px; left: 70px; background: white; transform: rotate(11deg); }
.note-front { top: 47px; left: 108px; background: white; transform: rotate(-7deg); }
.note-front i { color: #4285ff; font-size: 24px; font-style: normal; }
.note-front b { color: #303b4a; font-size: 13px; }
.art-spark { position: absolute; color: #78a4ff; }
.spark-one { top: 8px; right: 25px; font-size: 31px; }
.spark-two { right: 11px; bottom: 32px; color: #ffcc72; font-size: 22px; }
.list-toolbar { display: flex; align-items: end; justify-content: space-between; margin: 60px 8px 20px; }
.list-toolbar h2 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -.8px; }
.list-toolbar p { margin: 8px 0 0; color: #8b95a1; font-size: 13px; }
.category-tabs { display: flex; gap: 8px; overflow-x: auto; margin: 0 0 14px; padding: 0 0 8px; scrollbar-width: thin; }
.category-tabs button { min-height: 40px; flex: none; padding: 0 16px; border: 1px solid #e8ebef; border-radius: 22px; background: white; color: #596575; font-size: 13px; transition: background .15s, border-color .15s, color .15s; }
.category-tabs button[aria-pressed="true"] { border-color: #0064ff; background: #0064ff; color: white; font-weight: 600; }
.category-tabs button:focus-visible { outline: 3px solid #8db4ff; outline-offset: 2px; }
.sale-tabs { display: flex; width: fit-content; gap: 5px; margin: 4px 0 18px; padding: 4px; border-radius: 12px; background: #f2f4f7; }
.sale-tabs button { min-height: 36px; padding: 0 17px; border: 0; border-radius: 9px; background: transparent; color: #697586; font-size: 13px; font-weight: 600; }
.sale-tabs button[aria-pressed="true"] { background: white; color: #0064ff; box-shadow: 0 1px 4px #1822301a; }
.sale-tabs button:focus-visible { outline: 3px solid #8db4ff; outline-offset: 2px; }
.sort-label { display: flex; align-items: center; gap: 8px; padding: 10px 13px; border: 1px solid #e8ebef; border-radius: 10px; color: #596575; font-size: 12px; }
.sort-dot { width: 7px; height: 7px; border-radius: 50%; background: #4285ff; }
.post-list, .post-skeleton-list { padding: 0; border: 0; border-radius: 0; background: transparent; }
.post-list-row { min-height: 112px; gap: 14px; padding: 12px 14px; border-bottom: 1px solid #edf0f2; }
.post-list-row:hover { border-radius: 14px; background: #f8faff; }
.post-list-link { display: flex; min-width: 0; flex: 1; align-items: center; gap: 21px; color: inherit; text-decoration: none; }
.list-purchase-button { min-height: 38px; flex: none; padding: 0 15px; border-radius: 10px; font-size: 12px; }
.purchased-label { flex: none; color: #168566; font-size: 12px; font-weight: 700; }
.post-tile { display: grid; width: 68px; height: 68px; flex: none; place-items: center; border-radius: 18px; background: #edf3ff; color: #4d83ef; }
.post-tile span { font-size: 27px; }
.tile-1 { background: #eaf8f5; color: #39a88d; }
.tile-2 { background: #fff4e8; color: #edaa53; }
.tile-3 { background: #f3edff; color: #9670db; }
.post-copy { gap: 5px; }
.post-meta { color: #8b95a1; font-size: 11px; }
.post-category { margin-left: 9px; color: #4c78d8; }
.sale-badge { margin-left: 9px; color: #0064ff; font-weight: 700; }
.post-copy strong { color: #202a36; font-size: 16px; }
.post-copy .post-preview { color: #7b8794; font-size: 13px; }
.post-price { color: #0064ff; font-size: 12px; font-weight: 700; }
.post-chevron { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 50%; background: #f5f7fa; color: #667386; }
.more-button { min-height: 48px; margin-top: 25px; padding: 0 24px; border-radius: 12px; color: #596575; }
.empty-panel { min-height: 250px; border: 0; border-radius: 18px; background: #f7f8fa; }
.empty-panel .empty-symbol { width: 52px; height: 52px; border-radius: 18px; background: #eaf1ff; color: #4285ff; }
.post-skeleton-row { gap: 21px; border-bottom: 1px solid #edf0f2; }
.post-skeleton-row::before { width: 68px; height: 68px; flex: none; border-radius: 18px; background: #e9edf2; content: ''; }
.success-banner { border-radius: 12px; }
@media(max-width:760px) {
  .post-card-grid { grid-template-columns: 1fr; }
  .posts-page { padding: 0 24px 60px; }
  .list-hero { min-height: 340px; margin-top: 24px; padding: 40px 7%; }
  .hero-art { position: absolute; right: -115px; opacity: .48; }
  .hero-copy { max-width: 78%; }
  .list-toolbar { margin-top: 43px; }
}
@media(max-width:560px) {
  .posts-page { padding: 0 18px 48px; }
  .list-hero { min-height: 370px; align-items: start; margin-top: 18px; padding: 42px 25px; border-radius: 20px; }
  .hero-copy { max-width: 100%; }
  .list-hero h1 { font-size: 40px; letter-spacing: -2px; }
  .page-intro { max-width: 260px; font-size: 14px; }
  .hero-art { top: 162px; right: -173px; opacity: .27; }
  .create-link { min-height: 46px; }
  .list-toolbar { align-items: center; margin: 38px 0 15px; }
  .category-tabs { gap: 6px; margin-right: -18px; margin-left: -18px; padding: 0 18px 8px; }
  .category-tabs button { min-height: 37px; padding: 0 13px; font-size: 11px; }
  .list-toolbar h2 { font-size: 21px; }
  .list-toolbar p { max-width: 180px; font-size: 11px; }
  .sort-label { gap: 6px; padding: 8px; font-size: 10px; }
  .post-list-row { min-height: 91px; gap: 9px; padding: 10px 2px; }
  .post-list-link { gap: 13px; }
  .post-tile { width: 54px; height: 54px; border-radius: 15px; }
  .post-tile span { font-size: 22px; }
  .post-copy strong { font-size: 14px; }
  .post-copy .post-preview { font-size: 11px; }
  .post-chevron { width: 29px; height: 29px; flex: none; }
  .list-purchase-button { min-height: 34px; padding: 0 10px; font-size: 11px; }
}
@media(prefers-reduced-motion:reduce) { .post-list-row, .create-link { transition: none; } }
</style>
