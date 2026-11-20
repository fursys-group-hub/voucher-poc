"""PreToolUse 훅: 조회 API(call.py)를 부르는 명령이면 승인 창을 띄운다.

- 명령에 call.py 가 없으면 아무것도 하지 않는다 (다른 명령은 평소대로).
- call.py 호출이면 "물어보기"로 돌려보내고, 승인 창에 어떤 API를 어떤 조건으로 부르는지 쉬운 말로 보여 준다.
- 내용을 읽지 못해도 승인은 받는다 (안전한 쪽).
- 롤플레이 도구처럼 사람이 없는 실행은 환경변수 AUTO_SLIP_MAKER_NO_ASK=1 로 건너뛴다.
"""
import json
import os
import pathlib
import shlex
import sys

API_NAMES = {
    "slip/search": "전표 조회",
    "dept/search": "작성부서 조회",
    "account/search": "계정과목 조회",
    "costcenter/search": "코스트센터 조회",
    "manage/value/search": "관리항목 값 조회",
}
FIELD_NAMES = {
    "user_id": "작성자",
    "no_slip_serial": "전표번호",
    "keyword": "검색어",
    "from_dt": "시작일",
    "to_dt": "종료일",
    "company_code": "법인",
    "account_codes": "계정 코드",
    "cc_codes": "코스트센터 코드",
    "account_code": "계정",
    "manage_code": "관리항목",
    "value_codes": "값 코드",
    "context": "함께 보낸 값",
}


def ask(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=True))
    sys.exit(0)


def short(value, limit=60):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "…"


def describe(command, cwd):
    tokens = [t.strip("\"'") for t in shlex.split(command, posix=False)]
    idx = next(i for i, t in enumerate(tokens) if t.replace("\\", "/").endswith("call.py"))
    path = tokens[idx + 1].replace("\\", "/")
    if "/api/account/v1/" in path:
        path = path.split("/api/account/v1/", 1)[1]
    path = path.strip("/")
    name = API_NAMES.get(path, path)

    data_file = pathlib.Path(tokens[idx + 2])
    if not data_file.is_absolute():
        data_file = pathlib.Path(cwd) / data_file
    data = json.loads(data_file.read_text(encoding="utf-8-sig"))

    parts = []
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        label = FIELD_NAMES.get(key, key)
        if key == "user_id":
            value = "본인 (설정 파일의 ID)" if value == "$USER" else value
        parts.append(f"{label} {short(value)}")
    detail = ", ".join(parts) if parts else "조건 없음"
    return f"조회 API 호출: {name} — {detail}"


def main():
    if os.environ.get("AUTO_SLIP_MAKER_NO_ASK") == "1":
        return
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return
    command = (event.get("tool_input") or {}).get("command") or ""
    if "call.py" not in command:
        return
    try:
        ask(describe(command, event.get("cwd") or os.getcwd()))
    except SystemExit:
        raise
    except Exception:
        ask(f"조회 API 호출 (내용을 읽지 못했어요): {short(command, 200)}")


if __name__ == "__main__":
    main()
