import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import App from './App.vue';
import SignupPage from './pages/SignupPage.vue';
import LoginPage from './pages/LoginPage.vue';
import PostListPage from './pages/PostListPage.vue';
import PostCreatePage from './pages/PostCreatePage.vue';
import PostDetailPage from './pages/PostDetailPage.vue';
import { api } from './api';
import { postLoginNotice } from './navigationNotice';

jest.mock('./api', () => ({
  api: {
    listNotes: jest.fn(),
    getNote: jest.fn(),
    createNote: jest.fn(),
    signUp: jest.fn(),
    login: jest.fn(),
  },
}));

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
    api.listNotes.mockResolvedValue([]);
  });

  it('목록, 작성, 가입, 로그인 화면으로 각각 이동한다', async () => {
    const { router, wrapper } = await renderAt('/posts');
    expect(wrapper.text()).toContain('노트 모아보기');

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
    api.createNote.mockResolvedValue({ idx: 12, title: '작은 기쁨', contents: '따뜻한 차 한 잔' });
    api.getNote.mockResolvedValue({ idx: 12, title: '작은 기쁨', contents: '따뜻한 차 한 잔' });
    const { wrapper } = await renderAt('/posts/new');
    await wrapper.find('#post-title').setValue('작은 기쁨');
    await wrapper.find('#post-contents').setValue('따뜻한 차 한 잔');
    await wrapper.find('.writing-panel').trigger('submit');
    await flushPromises();

    expect(api.createNote).toHaveBeenCalledWith({ title: '작은 기쁨', contents: '따뜻한 차 한 잔' });
    expect(api.getNote).toHaveBeenCalledWith('12');
    expect(wrapper.text()).toContain('작은 기쁨');
  });

  it('번호로 상세 내용을 조회한다', async () => {
    api.getNote.mockResolvedValue({ idx: 9, title: '오래된 기억', contents: '비가 오던 날' });
    const { wrapper } = await renderAt('/posts/9');

    expect(api.getNote).toHaveBeenCalledWith('9');
    expect(wrapper.text()).toContain('오래된 기억');
    expect(wrapper.text()).toContain('비가 오던 날');
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
    expect(wrapper.text()).toContain('노트 모아보기');
  });
});
