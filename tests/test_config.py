from pathlib import Path

from app.core.config import Settings


def test_production_kakao_callback_default():
    loaded = Settings(_env_file=None)

    assert loaded.KAKAO_REDIRECT_URI == "https://api.aiready.p-e.kr/api/user/kakao/callback"


def test_settings_load_shared_env_file_from_project_root():
    expected_env_file = Path(__file__).resolve().parents[1] / ".env"

    assert Path(Settings.model_config["env_file"]).resolve() == expected_env_file


def test_settings_accept_frontend_variables_in_shared_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "KAKAO_REST_API_KEY=test-rest-key\n"
        "KAKAO_CLIENT_SECRET=test-client-secret\n"
        "KAKAO_REDIRECT_URI=https://example.test/callback\n"
        "VITE_KAKAO_JS_KEY=test-js-key\n",
        encoding="utf-8",
    )

    loaded = Settings(_env_file=env_file)

    assert loaded.KAKAO_REST_API_KEY == "test-rest-key"
    assert loaded.KAKAO_CLIENT_SECRET == "test-client-secret"
    assert loaded.KAKAO_REDIRECT_URI == "https://example.test/callback"
