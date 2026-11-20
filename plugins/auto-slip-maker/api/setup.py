"""설정 파일 준비. 사용: python -X utf8 setup.py

- 설정 파일 ~/.auto-slip-maker/api.env 가 없으면 빈 칸으로 만든다. 파일에 없는 칸은 빈 칸으로 덧붙인다.
- 빈 칸이 있으면 메모장으로 열어 준다 (Windows).
- 칸마다 채워졌는지만 출력한다. 값은 출력하지 않는다.
- 환경변수에 값이 있으면 채워진 것으로 본다 (call.py와 같은 순서).
- 롤플레이 도구처럼 사람이 없는 실행(AUTO_SLIP_MAKER_NO_ASK=1)에서는 메모장을 열지 않는다.
"""
import os
import pathlib
import subprocess

SETTINGS_FILE = pathlib.Path.home() / ".auto-slip-maker" / "api.env"

FIELDS = [
    ("ACCOUNTAPI_URL", "서버 주소", "경영정보시스템 개발팀에서 받은 값"),
    ("ACCOUNTAPI_KEY", "인증키", "경영정보시스템 개발팀에서 받은 값"),
    ("ACCOUNTAPI_IDENTIFIER", "호출 식별자", "경영정보시스템 개발팀에서 받은 값"),
    ("ACCOUNTAPI_USER_ID", "작성자 ID", "본인 account 로그인 ID"),
]

HEADER = "# 반복 전표 자동화 설정 파일입니다. 각 줄의 = 뒤에 값을 넣고 저장해 주세요.\n"


def field_lines(name, label, hint):
    return f"\n# {label} ({hint})\n{name}=\n"


def read_values(text):
    """call.py와 같은 규칙: 한 줄에 이름=값. 이름이 있는 줄은 값이 비어도 담는다."""
    values = {}
    for line in text.splitlines():
        key, sep, value = line.strip().partition("=")
        if sep:
            values[key.strip()] = value.strip()
    return values


def open_editor(path):
    if os.name != "nt" or os.environ.get("AUTO_SLIP_MAKER_NO_ASK") == "1":
        return False
    try:
        subprocess.Popen(["notepad.exe", str(path)],
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                         close_fds=True)
        return True
    except OSError:
        return False


def main():
    created = False
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(HEADER + "".join(field_lines(*f) for f in FIELDS), encoding="utf-8")
        created = True

    try:
        text = SETTINGS_FILE.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        opened = open_editor(SETTINGS_FILE)
        print(f"설정 파일: {SETTINGS_FILE}")
        print("결과: 읽지 못함. 파일이 UTF-8이 아닌 형식으로 저장돼 있어요.")
        print("메모장에서 [다른 이름으로 저장] → 인코딩을 UTF-8로 골라 같은 이름으로 저장해 주세요."
              + (" 메모장으로 열었어요." if opened else ""))
        return

    values = read_values(text)

    # 파일에 없는 칸은 빈 칸으로 덧붙인다 (환경변수로 채운 칸은 제외)
    missing = [f for f in FIELDS if f[0] not in values and not os.environ.get(f[0])]
    if missing:
        with SETTINGS_FILE.open("a", encoding="utf-8") as fp:
            if not text.endswith("\n"):
                fp.write("\n")
            fp.write("".join(field_lines(*f) for f in missing))

    empty = 0
    lines = []
    for name, label, _ in FIELDS:
        if os.environ.get(name):
            state = "채워짐 (환경변수)"
        elif values.get(name):
            state = "채워짐"
        else:
            state = "비어 있음"
            empty += 1
        lines.append(f"- {label} ({name}): {state}")

    print(f"설정 파일: {SETTINGS_FILE}" + (" (방금 만들었어요)" if created else ""))
    print("\n".join(lines))
    if empty:
        opened = open_editor(SETTINGS_FILE)
        print(f"결과: 빈 칸 {empty}개." + (" 메모장으로 열었어요." if opened else " 위 주소의 파일을 메모장으로 열어 채워 주세요."))
    else:
        print("결과: 모두 채워짐")


if __name__ == "__main__":
    main()
