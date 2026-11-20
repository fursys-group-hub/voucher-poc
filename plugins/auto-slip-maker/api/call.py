"""accountapi 호출 (개발서버). 사용: python -X utf8 call.py <API 경로> <요청 data JSON 파일>

- API 경로는 /api/account/v1/ 뒤 부분만 쓴다 (예: slip/search). Git Bash가 /로 시작하는 인자를 파일 경로로 바꾸기 때문이다.
- 서버 주소·인증키·호출 식별자·작성자 ID(ACCOUNTAPI_URL, ACCOUNTAPI_KEY, ACCOUNTAPI_IDENTIFIER, ACCOUNTAPI_USER_ID)는
  환경변수에서, 없으면 설정 파일 ~/.auto-slip-maker/api.env (한 줄에 이름=값) 에서 읽는다. 값은 출력하지 않는다.
- 요청 data 안의 "$USER"는 ACCOUNTAPI_USER_ID 값으로 바꾼다.
- 응답 JSON을 그대로 출력한다.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

SETTINGS_FILE = pathlib.Path.home() / ".auto-slip-maker" / "api.env"


def setting(name):
    """환경변수 → 설정 파일 순서로 값을 찾는다. 없으면 None."""
    if os.environ.get(name):
        return os.environ[name]
    if SETTINGS_FILE.exists():
        for line in SETTINGS_FILE.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key.strip() == name and value.strip():
                return value.strip()
    return None


def main():
    if len(sys.argv) != 3:
        sys.exit("사용: python -X utf8 call.py <API 경로 (예: slip/search)> <요청 data JSON 파일>")
    path, data_file = sys.argv[1].replace("\\", "/"), sys.argv[2]
    if "/api/" in path:                      # 전체 경로를 넣었거나 Git Bash가 앞에 경로를 붙인 경우
        path = path[path.index("/api/"):]
    else:
        path = "/api/account/v1/" + path.strip("/")

    base = setting("ACCOUNTAPI_URL")
    key = setting("ACCOUNTAPI_KEY")
    identifier = setting("ACCOUNTAPI_IDENTIFIER")
    missing = [name for name, value in (("ACCOUNTAPI_URL", base), ("ACCOUNTAPI_KEY", key),
                                        ("ACCOUNTAPI_IDENTIFIER", identifier)) if not value]
    if missing:
        sys.exit(f"개발 환경 설정이 안 됐습니다: {SETTINGS_FILE} 에 {', '.join(missing)}가 없습니다.")
    base = base.rstrip("/")

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("user_id") == "$USER":
        user = setting("ACCOUNTAPI_USER_ID")
        if not user:
            sys.exit(f"개발 환경 설정이 안 됐습니다: {SETTINGS_FILE} 에 ACCOUNTAPI_USER_ID가 없습니다.")
        data["user_id"] = user

    body = {"authentication_key": key, "identifier_id": identifier, "data": data}
    req = urllib.request.Request(base + path, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
    except urllib.error.URLError as e:
        sys.exit(f"서버에 연결할 수 없습니다 ({base}): {e.reason}")

    try:
        print(json.dumps(json.loads(raw), ensure_ascii=False, indent=1))
    except ValueError:
        print(raw.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
