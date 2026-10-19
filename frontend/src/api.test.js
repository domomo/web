import { api } from './api';

describe('FastAPI client contract', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('uses the paginated board list route', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => [] });

    await api.listNotes(20, 10);

    expect(global.fetch).toHaveBeenCalledWith('/api/board/list?offset=20&limit=10', expect.objectContaining({ credentials: 'same-origin' }));
  });

  it('sends board writes as JSON using the backend field names', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: async () => ({ idx: 1, title: '제목', contents: '내용' }) });

    await api.createNote({ title: '제목', contents: '내용' });

    expect(global.fetch).toHaveBeenCalledWith('/api/board/write', expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '제목', contents: '내용' }),
    }));
  });

  it('turns FastAPI validation details into a readable error', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ msg: 'Field required' }] }) });

    await expect(api.getNote(3)).rejects.toThrow('Field required');
  });
});
