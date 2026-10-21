import { getKakaoSdk } from './api/kakao';

describe('Kakao JavaScript SDK setup', () => {
  beforeEach(() => {
    document.head.innerHTML = '<meta name="kakao-js-key" content="javascript-key">';
    let ready = false;
    window.Kakao = {
      init: jest.fn(function init() {
        ready = true;
        this.Auth = { authorize: jest.fn() };
      }),
      isInitialized: jest.fn(() => ready),
    };
  });

  afterEach(() => {
    delete window.Kakao;
  });

  it('initializes once with the public JavaScript key', () => {
    const first = getKakaoSdk();
    const second = getKakaoSdk();

    expect(first).toBe(window.Kakao);
    expect(second).toBe(window.Kakao);
    expect(window.Kakao.init).toHaveBeenCalledTimes(1);
    expect(window.Kakao.init).toHaveBeenCalledWith('javascript-key');
  });

  it('initializes the SDK before checking for the Auth module', () => {
    const sdk = getKakaoSdk();

    expect(sdk.Auth.authorize).toEqual(expect.any(Function));
    expect(sdk.init).toHaveBeenCalledWith('javascript-key');
  });

  it('reports a missing JavaScript key or SDK script', () => {
    document.head.innerHTML = '<meta name="kakao-js-key" content="">';
    expect(() => getKakaoSdk()).toThrow('카카오 로그인을 설정할 수 없어요.');
    document.head.innerHTML = '<meta name="kakao-js-key" content="javascript-key">';
    delete window.Kakao;
    expect(() => getKakaoSdk()).toThrow('카카오 로그인을 불러오지 못했어요.');
  });
});
