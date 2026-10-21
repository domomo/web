const API_BASE_URL = (globalThis.__API_BASE_URL__ || 'https://api.aiready.p-e.kr').replace(/\/$/, '');

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
    credentials: 'include',
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map((issue) => issue.msg).join(', ')
      : data?.detail;
    const error = new Error(detail || `요청을 처리하지 못했어요. (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}

const json = (body) => ({ method: 'POST', body: JSON.stringify(body) });

export const api = {
  listNotes: (offset = 0, limit = 20, category, saleType) => {
    const categoryQuery = category ? `&category=${encodeURIComponent(category)}` : '';
    const saleQuery = saleType ? `&sale_type=${encodeURIComponent(saleType)}` : '';
    return request(`/board/list?offset=${offset}&limit=${limit}${categoryQuery}${saleQuery}`);
  },
  getNote: (idx) => request(`/board/read/${encodeURIComponent(idx)}`),
  createNote: (note) => request('/board/write', json(note)),
  getPaymentConfig: () => request('/purchases/config'),
  preparePurchase: (boardIdx) => request('/purchases/prepare', json({ board_idx: boardIdx })),
  confirmPurchase: (paymentId) => request('/purchases/confirm', json({ payment_id: paymentId })),
  signUp: (account) => request('/user/signup', json(account)),
  login: (account) => request('/user/login', json(account)),
  logout: () => request('/user/logout', { method: 'POST' }),
  getCurrentUser: () => request('/user/me'),
  getKakaoLoginState: () => request('/user/kakao/state'),
};

export { request };
