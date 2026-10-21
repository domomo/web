import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import App from './components/App.vue';
import SignupPage from './views/SignupPage.vue';
import LoginPage from './views/LoginPage.vue';
import PostListPage from './views/PostListPage.vue';
import PostCreatePage from './views/PostCreatePage.vue';
import PostDetailPage from './views/PostDetailPage.vue';
import { api } from './api/api';
import { postLoginNotice } from './stores/navigationNotice';

jest.mock('./api/api', () => ({
  api: {
    listNotes: jest.fn(),
    getNote: jest.fn(),
    getPaymentConfig: jest.fn(),
    preparePurchase: jest.fn(),
    confirmPurchase: jest.fn(),
    createNote: jest.fn(),
    signUp: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    getKakaoLoginState: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));

jest.mock('@portone/browser-sdk/v2', () => ({
  requestPayment: jest.fn().mockResolvedValue({ paymentId: 'article-payment-1' }),
}), { virtual: true });

jest.mock('./api/kakao', () => ({ getKakaoSdk: jest.fn() }));
import { getKakaoSdk } from './api/kakao';

const routes = [
  { path: '/', redirect: '/posts' },
  { path: '/signup', name: 'signup', component: SignupPage },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/posts', name: 'post-list', component: PostListPage },
  { path: '/posts/new', name: 'post-create', component: PostCreatePage },
  { path: '/posts/:idx(\\d+)', name: 'post-detail', component: PostDetailPage },
];

async function renderAt(path) {
  const router = createRouter({ history: createMemoryHistory(), routes });
  await router.push(path);
  await router.isReady();
  const wrapper = mount(App, { global: { plugins: [router] } });
  await flushPromises();
  return { router, wrapper };
}

describe('여백 페이지 흐름', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    postLoginNotice.value = false;
    api.getCurrentUser.mockRejectedValue(new Error('not signed in'));
    api.listNotes.mockResolvedValue([]);
    api.getPaymentConfig.mockResolvedValue({ configured: true, store_id: 'store-test', channel_key: 'channel-test' });
    api.preparePurchase.mockResolvedValue({ payment_id: 'article-payment-1', order_name: '유료 글', amount: 3900 });
    api.confirmPurchase.mockResolvedValue({ id: 1, board_idx: 4, price: 3900 });
  });

  it('목록, 작성, 가입, 로그인 화면으로 각각 이동한다', async () => {
    const { router, wrapper } = await renderAt('/posts');
    expect(wrapper.text()).toContain('기록은 가볍게,');

    await router.push('/posts/new');
    await flushPromises();
    expect(wrapper.text()).toContain('새 노트');

    await router.push('/signup');
    await flushPromises();
    expect(wrapper.text()).toContain('여백 만들기');

    await router.push('/login');
    await flushPromises();
    expect(wrapper.text()).toContain('로그인');
  });

  it('목록 API 결과를 표시하고 더 보기 요청으로 다음 페이지를 붙인다', async () => {
    const firstPage = Array.from({ length: 20 }, (_, index) => ({
      idx: 20 - index,
      title: index === 0 ? '산책' : `노트 ${index + 1}`,
      contents: '바람이 좋았다.',
    }));
    api.listNotes
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce([{ idx: 3, title: '느린 아침', contents: '창문을 열었다.' }]);
    const { wrapper } = await renderAt('/posts');

    expect(api.listNotes).toHaveBeenCalledWith(0, 20);
    expect(wrapper.text()).toContain('산책');
    await wrapper.find('.more-button').trigger('click');
    await flushPromises();
    expect(api.listNotes).toHaveBeenLastCalledWith(20, 20);
    expect(wrapper.text()).toContain('느린 아침');
  });

  it('분야 탭을 바꾸면 해당 분야 첫 페이지를 불러온다', async () => {
    api.listNotes.mockResolvedValueOnce([]).mockResolvedValueOnce([
      { idx: 3, title: '새로운 발견', contents: '실험을 시작했다.', category: '과학/IT' },
    ]);
    const { wrapper } = await renderAt('/posts');

    await wrapper.findAll('.category-tabs button')[2].trigger('click');
    await flushPromises();

    expect(api.listNotes).toHaveBeenLastCalledWith(0, 20, '과학/IT');
    expect(wrapper.find('.list-toolbar h2').text()).toBe('과학/IT');
    expect(wrapper.text()).toContain('새로운 발견');
  });

  it('무료와 유료 탭이 서버 목록 필터를 바꾼다', async () => {
    api.listNotes.mockResolvedValue([]);
    const { wrapper } = await renderAt('/posts');

    await wrapper.find('.sale-tabs button[aria-selected="false"]:nth-child(2)').trigger('click');
    await flushPromises();
    expect(api.listNotes).toHaveBeenLastCalledWith(0, 20, undefined, 'free');

    await wrapper.find('.sale-tabs button:nth-child(3)').trigger('click');
    await flushPromises();
    expect(api.listNotes).toHaveBeenLastCalledWith(0, 20, undefined, 'paid');
  });

  it('목록 오류를 재시도해 다시 불러온다', async () => {
    api.listNotes.mockRejectedValueOnce(new Error('network unavailable')).mockResolvedValueOnce([]);
    const { wrapper } = await renderAt('/posts');
    expect(wrapper.text()).toContain('목록을 불러오지 못했어요.');

    await wrapper.find('.empty-panel button').trigger('click');
    await flushPromises();
    expect(api.listNotes).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain('아직 기록이 없어요.');
  });

  it('목록 데이터가 도착하기 전 목록 스켈레톤을 표시한다', async () => {
    api.listNotes.mockReturnValue(new Promise(() => {}));
    const { wrapper } = await renderAt('/posts');

    expect(wrapper.find('.post-skeleton-list').exists()).toBe(true);
    wrapper.unmount();
  });

  it('게시글을 저장하고 저장된 글의 상세 화면으로 이동한다', async () => {
    api.createNote.mockResolvedValue({ idx: 12, title: '작은 기쁨', contents: '따뜻한 차 한 잔', category: '예술/취미' });
    api.getNote.mockResolvedValue({ idx: 12, title: '작은 기쁨', contents: '따뜻한 차 한 잔', category: '예술/취미' });
    const { wrapper } = await renderAt('/posts/new');
    await wrapper.find('#post-title').setValue('작은 기쁨');
    await wrapper.find('#post-category').setValue('예술/취미');
    await wrapper.find('#post-contents').setValue('따뜻한 차 한 잔');
    await wrapper.find('.writing-panel').trigger('submit');
    await flushPromises();

    expect(api.createNote).toHaveBeenCalledWith({ title: '작은 기쁨', contents: '따뜻한 차 한 잔', category: '예술/취미' });
    expect(api.getNote).toHaveBeenCalledWith('12');
    expect(wrapper.text()).toContain('작은 기쁨');
  });

  it('유료 글 작성은 가격과 미리보기 필드를 payload에 포함한다', async () => {
    api.createNote.mockResolvedValue({ idx: 13, title: '유료 기록', contents: '본문', category: '예술/취미' });
    api.getNote.mockResolvedValue({ idx: 13, title: '유료 기록', contents: '본문', category: '예술/취미' });
    const { wrapper } = await renderAt('/posts/new');
    await wrapper.get('#post-title').setValue('유료 기록');
    await wrapper.get('#post-category').setValue('예술/취미');
    await wrapper.get('#post-contents').setValue('본문');
    await wrapper.get('input[value="paid"]').setValue(true);
    await wrapper.get('#post-price').setValue('3900');
    await wrapper.get('#post-preview').setValue('공개 미리보기');
    await wrapper.get('.writing-panel').trigger('submit');
    await flushPromises();

    expect(api.createNote).toHaveBeenCalledWith({ title: '유료 기록', contents: '본문', category: '예술/취미', sale_price: 3900, preview: '공개 미리보기' });
  });

  it('번호로 상세 내용을 조회한다', async () => {
    api.getNote.mockResolvedValue({ idx: 9, title: '오래된 기억', contents: '비가 오던 날', category: '인문/교양' });
    const { wrapper } = await renderAt('/posts/9');

    expect(api.getNote).toHaveBeenCalledWith('9');
    expect(wrapper.text()).toContain('오래된 기억');
    expect(wrapper.text()).toContain('비가 오던 날');
    expect(wrapper.text()).toContain('인문/교양');
  });

  it('판매 글 목록에 미리보기와 가격을 표시한다', async () => {
    api.listNotes.mockResolvedValue([{ idx: 4, title: '유료 글', contents: null, preview: '첫 문단만 공개합니다.', sale_price: 3900, is_for_sale: true }]);
    const { wrapper } = await renderAt('/posts');

    expect(wrapper.text()).toContain('첫 문단만 공개합니다.');
    expect(wrapper.text()).toContain('3,900원');
    expect(wrapper.get('.list-purchase-button').text()).toBe('구매하기');
  });

  it('글 목록의 구매하기가 포트원 결제 후 해당 글을 연다', async () => {
    api.listNotes.mockResolvedValue([{ idx: 4, title: '유료 글', contents: null, preview: '미리보기', sale_price: 3900, is_for_sale: true }]);
    api.confirmPurchase.mockResolvedValue({ id: 1, board_idx: 4, price: 3900 });
    window.history.pushState({}, '', '/posts');
    const { wrapper, router } = await renderAt('/posts');

    await wrapper.get('.list-purchase-button').trigger('click');
    await flushPromises();

    expect(api.preparePurchase).toHaveBeenCalledWith(4);
    expect(api.confirmPurchase).toHaveBeenCalledWith('article-payment-1');
    expect(router.currentRoute.value.name).toBe('post-detail');
    expect(router.currentRoute.value.params.idx).toBe('4');
  });

  it('잠긴 상세는 본문 대신 미리보기와 구매 버튼을 보여준다', async () => {
    api.getNote.mockResolvedValue({ idx: 4, title: '유료 글', contents: null, preview: '공개 미리보기', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: false });
    const { wrapper } = await renderAt('/posts/4');

    expect(wrapper.text()).toContain('공개 미리보기');
    expect(wrapper.text()).toContain('3,900원');
    expect(wrapper.get('[data-testid="purchase-note"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain('본문 전체');
  });

  it('포트원 설정이 없으면 구매 버튼을 비활성화한다', async () => {
    api.getPaymentConfig.mockResolvedValue({ configured: false });
    api.getNote.mockResolvedValue({ idx: 4, title: '유료 글', contents: null, preview: '공개 미리보기', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: false });
    const { wrapper } = await renderAt('/posts/4');

    expect(wrapper.get('[data-testid="purchase-note"]').attributes('disabled')).toBeDefined();
    expect(wrapper.text()).toContain('결제 설정이 준비되면 구매할 수 있어요.');
  });

  it('구매 성공 후 상세를 다시 불러와 본문을 표시한다', async () => {
    api.getNote.mockResolvedValueOnce({ idx: 4, title: '유료 글', contents: null, preview: '공개 미리보기', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: false });
    api.getNote.mockResolvedValueOnce({ idx: 4, title: '유료 글', contents: '구매한 본문 전체', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: true });
    const { wrapper } = await renderAt('/posts/4');

    await wrapper.get('[data-testid="purchase-note"]').trigger('click');
    await flushPromises();

    expect(api.preparePurchase).toHaveBeenCalledWith('4');
    expect(api.confirmPurchase).toHaveBeenCalledWith('article-payment-1');
    expect(api.getNote).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain('구매한 본문 전체');
  });

  it('구매가 401이면 로그인 안내를 표시한다', async () => {
    api.getNote.mockResolvedValue({ idx: 4, title: '유료 글', contents: null, preview: '공개 미리보기', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: false });
    const unauthorized = new Error('인증이 필요합니다.');
    unauthorized.status = 401;
    api.preparePurchase.mockRejectedValue(unauthorized);
    const { wrapper } = await renderAt('/posts/4');

    await wrapper.get('[data-testid="purchase-note"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain('인증이 필요합니다.');
    expect(wrapper.get('.detail-copy a[href="/login"]').text()).toContain('로그인하기');
  });

  it('작성자와 구매자는 구매 CTA를 보지 않는다', async () => {
    api.getNote.mockResolvedValue({ idx: 4, title: '유료 글', contents: '본문', sale_price: 3900, is_for_sale: true, is_author: true, has_purchased: false });
    const authorView = await renderAt('/posts/4');
    expect(authorView.wrapper.find('[data-testid="purchase-note"]').exists()).toBe(false);
    authorView.wrapper.unmount();

    api.getNote.mockResolvedValue({ idx: 4, title: '유료 글', contents: '본문', sale_price: 3900, is_for_sale: true, is_author: false, has_purchased: true });
    const buyerView = await renderAt('/posts/4');
    expect(buyerView.wrapper.find('[data-testid="purchase-note"]').exists()).toBe(false);
    buyerView.wrapper.unmount();
  });

  it('상세 데이터가 도착하기 전 상세 스켈레톤을 표시한다', async () => {
    api.getNote.mockReturnValue(new Promise(() => {}));
    const { wrapper } = await renderAt('/posts/9');

    expect(wrapper.find('.detail-skeleton').exists()).toBe(true);
    wrapper.unmount();
  });

  it('가입 후 로그인 페이지에 완료 안내를 전달한다', async () => {
    api.signUp.mockResolvedValue({ email: 'hello@example.com', name: '지민' });
    const { wrapper } = await renderAt('/signup');
    await wrapper.find('#signup-name').setValue('지민');
    await wrapper.find('#signup-email').setValue('hello@example.com');
    await wrapper.find('#signup-password').setValue('secret');
    await wrapper.find('.page-form').trigger('submit');
    await flushPromises();

    expect(api.signUp).toHaveBeenCalledWith({ email: 'hello@example.com', name: '지민', password: 'secret' });
    expect(wrapper.text()).toContain('가입이 완료됐어요.');
  });

  it('로그인에 성공하면 노트 목록으로 이동한다', async () => {
    api.login.mockResolvedValue({ email: 'hello@example.com' });
    const { wrapper } = await renderAt('/login');
    await wrapper.find('#login-email').setValue('hello@example.com');
    await wrapper.find('#login-password').setValue('secret');
    await wrapper.find('.page-form').trigger('submit');
    await flushPromises();

    expect(api.login).toHaveBeenCalledWith({ email: 'hello@example.com', password: 'secret' });
    expect(wrapper.text()).toContain('로그인했어요.');
    expect(wrapper.text()).toContain('기록은 가볍게,');
    expect(wrapper.get('[data-testid="user-profile"]').text()).toContain('님');
    expect(wrapper.text()).not.toContain('회원가입');
  });

  it('로그아웃에 성공하면 계정 메뉴를 다시 표시한다', async () => {
    api.getCurrentUser.mockResolvedValue({ email: 'hello@example.com', name: '지민' });
    api.logout.mockResolvedValue({ message: '로그아웃되었습니다.' });
    const { wrapper } = await renderAt('/posts');

    expect(wrapper.get('[data-testid="user-profile"]').text()).toContain('지민님');
    await wrapper.get('.logout-button').trigger('click');
    await flushPromises();

    expect(api.logout).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('로그인');
    expect(wrapper.text()).toContain('회원가입');
    expect(wrapper.find('[data-testid="user-profile"]').exists()).toBe(false);
  });

  it('로그아웃에 실패하면 계정 상태를 유지하고 오류를 알린다', async () => {
    api.getCurrentUser.mockResolvedValue({ email: 'hello@example.com', name: '지민' });
    api.logout.mockRejectedValue(new Error('network unavailable'));
    const { wrapper } = await renderAt('/posts');

    await wrapper.get('.logout-button').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="user-profile"]').text()).toContain('지민님');
    expect(wrapper.get('[role="alert"]').text()).toContain('로그아웃하지 못했어요.');
    expect(wrapper.text()).not.toContain('회원가입');
  });

  it('Kakao state와 프로필 닉네임 범위로 authorize를 호출한다', async () => {
    const sdk = { Auth: { authorize: jest.fn() } };
    api.getKakaoLoginState.mockResolvedValue({ state: 'safe-state', redirect_uri: 'http://localhost/callback' });
    getKakaoSdk.mockReturnValue(sdk);
    const { wrapper } = await renderAt('/login');

    await wrapper.get('[data-testid="kakao-login"]').trigger('click');
    await flushPromises();

    expect(sdk.Auth.authorize).toHaveBeenCalledWith({
      redirectUri: 'http://localhost/callback',
      scope: 'profile_nickname',
      state: 'safe-state',
    });
  });

  it('Kakao SDK 설정 오류를 접근 가능한 메시지로 보여준다', async () => {
    api.getKakaoLoginState.mockResolvedValue({ state: 's', redirect_uri: 'http://localhost/callback' });
    getKakaoSdk.mockImplementation(() => { throw new Error('sdk failed'); });
    const { wrapper } = await renderAt('/login');

    await wrapper.get('[data-testid="kakao-login"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[role="alert"]').text()).toContain('카카오 로그인을 시작하지 못했어요.');
  });

  it('Kakao 로그인 취소를 고정된 안내로 표시한다', async () => {
    const { wrapper } = await renderAt('/login?oauth_error=cancelled');
    expect(wrapper.get('[role="alert"]').text()).toContain('카카오 로그인을 취소했어요.');
  });
});
