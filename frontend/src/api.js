async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
    credentials: 'same-origin',
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map((issue) => issue.msg).join(', ')
      : data?.detail;
    throw new Error(detail || `요청을 처리하지 못했어요. (${response.status})`);
  }
  return data;
}

const json = (body) => ({ method: 'POST', body: JSON.stringify(body) });

export const api = {
  listNotes: (offset = 0, limit = 20) =>
    request(`/board/list?offset=${offset}&limit=${limit}`),
  getNote: (idx) => request(`/board/read/${encodeURIComponent(idx)}`),
  createNote: (note) => request('/board/write', json(note)),
  signUp: (account) => request('/user/signup', json(account)),
  login: (account) => request('/user/login', json(account)),
};

export { request };
