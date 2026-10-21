import { api } from './api/api';

describe('FastAPI client contract', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('uses the paginated board list route', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });

    await api.listNotes(20, 10);

    expect(global.fetch).toHaveBeenCalledWith('/api/board/list?offset=20&limit=10', expect.objectContaining({ credentials: 'same-origin' }));
  });

  it('filters the paginated board list by an encoded category', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });

    await api.listNotes(0, 20, '경제/경영');

    expect(global.fetch).toHaveBeenCalledWith('/api/board/list?offset=0&limit=20&category=%EA%B2%BD%EC%A0%9C%2F%EA%B2%BD%EC%98%81', expect.objectContaining({ credentials: 'same-origin' }));
  });

  it('filters the paginated board list by sale type', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });

    await api.listNotes(0, 20, undefined, 'paid');

    expect(global.fetch).toHaveBeenCalledWith('/api/board/list?offset=0&limit=20&sale_type=paid', expect.any(Object));
  });

  it('sends board writes as JSON using the backend field names', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ idx: 1, title: '제목', contents: '내용', category: '경제/경영' }) });

    await api.createNote({ title: '제목', contents: '내용', category: '경제/경영' });

    expect(global.fetch).toHaveBeenCalledWith('/api/board/write', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '제목', contents: '내용', category: '경제/경영' }),
    }));
  });

  it('sends paid fields unchanged when creating a paid note', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ idx: 1 }) });

    await api.createNote({ title: '유료 글', contents: '본문', category: '인문/교양', sale_price: 3900, preview: '공개 미리보기' });

    expect(global.fetch).toHaveBeenCalledWith('/api/board/write', expect.objectContaining({
      body: JSON.stringify({ title: '유료 글', contents: '본문', category: '인문/교양', sale_price: 3900, preview: '공개 미리보기' }),
    }));
  });

  it('creates a server-priced payment order with same-origin credentials', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ payment_id: 'article-1' }) });

    await api.preparePurchase(9);

    expect(global.fetch).toHaveBeenCalledWith('/api/purchases/prepare', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ board_idx: 9 }),
      credentials: 'same-origin',
    }));
  });

  it('confirms a PortOne payment by payment id', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ id: 2 }) });

    await api.confirmPurchase('article-1');

    expect(global.fetch).toHaveBeenCalledWith('/api/purchases/confirm', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ payment_id: 'article-1' }),
      credentials: 'same-origin',
    }));
  });

  it('turns FastAPI validation details into a readable error', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ msg: 'Field required' }] }) });

    await expect(api.getNote(3)).rejects.toThrow('Field required');
  });

  it('preserves the HTTP status on readable API errors', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: '인증이 필요합니다.' }) });

    await expect(api.getNote(3)).rejects.toMatchObject({ message: '인증이 필요합니다.', status: 401 });
  });

  it('requests state before Kakao authorization with same-origin cookies', async () => {
    const state = { state: 'random-state', redirect_uri: 'http://localhost:8000/api/user/kakao/callback' };
    global.fetch.mockResolvedValue({ ok: true, json: async () => state });

    await expect(api.getKakaoLoginState()).resolves.toEqual(state);

    expect(global.fetch).toHaveBeenCalledWith('/api/user/kakao/state', expect.objectContaining({
      credentials: 'same-origin',
    }));
  });

  it('retrieves the signed-in user using the session cookie', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ email: null, name: '카카오 사용자' }) });

    await expect(api.getCurrentUser()).resolves.toEqual({ email: null, name: '카카오 사용자' });
    expect(global.fetch).toHaveBeenCalledWith('/api/user/me', expect.objectContaining({ credentials: 'same-origin' }));
  });

  it('clears the signed-in session through the logout endpoint', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ message: '로그아웃되었습니다.' }) });

    await expect(api.logout()).resolves.toEqual({ message: '로그아웃되었습니다.' });

    expect(global.fetch).toHaveBeenCalledWith('/api/user/logout', expect.objectContaining({
      method: 'POST',
      credentials: 'same-origin',
    }));
  });
});
