from dataclasses import dataclass

import httpx


TOKEN_URL = "https://kauth.kakao.com/oauth/token"
USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoOAuthError(Exception):
    """A safe, normalized Kakao provider failure."""


@dataclass(frozen=True)
class KakaoProfile:
    user_id: str
    nickname: str


class KakaoOAuthClient:
    def __init__(self, rest_api_key: str | None, client_secret: str | None,
                 redirect_uri: str, client: httpx.Client | None = None,
                 token_url: str = TOKEN_URL, user_info_url: str = USER_INFO_URL):
        self.rest_api_key = rest_api_key
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.user_info_url = user_info_url
        self.client = client or httpx.Client(timeout=10.0)
        self._owns_client = client is None

    def close(self):
        if self._owns_client:
            self.client.close()

    def user_from_code(self, code: str) -> KakaoProfile:
        if not self.rest_api_key:
            raise KakaoOAuthError("provider_unavailable")
        try:
            form = {
                "grant_type": "authorization_code",
                "client_id": self.rest_api_key,
                "redirect_uri": self.redirect_uri,
                "code": code,
            }
            if self.client_secret:
                form["client_secret"] = self.client_secret
            token_response = self.client.post(self.token_url, data=form)
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise KakaoOAuthError("provider_error")

            user_response = self.client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
                params={"property_keys": '["kakao_account.profile"]'},
            )
            user_response.raise_for_status()
            payload = user_response.json()
            account_id = payload.get("id")
            nickname = payload.get("kakao_account", {}).get("profile", {}).get("nickname")
            if account_id is None or not isinstance(nickname, str) or not nickname.strip():
                raise KakaoOAuthError("profile_incomplete")
            return KakaoProfile(str(account_id), nickname.strip())
        except KakaoOAuthError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError) as exc:
            raise KakaoOAuthError("provider_error") from exc
