let initializedSdk = null;

export function getKakaoSdk() {
  const key = document.querySelector('meta[name="kakao-js-key"]')?.content?.trim();
  if (!key || key.includes('%VITE_KAKAO_JS_KEY%')) {
    throw new Error('카카오 로그인을 설정할 수 없어요.');
  }

  const sdk = window.Kakao;
  if (!sdk || typeof sdk.init !== 'function' || typeof sdk.isInitialized !== 'function') {
    throw new Error('카카오 로그인을 불러오지 못했어요.');
  }
  if (initializedSdk === sdk || sdk.isInitialized()) {
    if (!sdk.Auth?.authorize) throw new Error('카카오 로그인을 불러오지 못했어요.');
    initializedSdk = sdk;
    return sdk;
  }

  try {
    sdk.init(key);
    if (!sdk.isInitialized() || !sdk.Auth?.authorize) throw new Error('SDK initialization failed');
    initializedSdk = sdk;
    return sdk;
  } catch {
    throw new Error('카카오 로그인을 불러오지 못했어요.');
  }
}
