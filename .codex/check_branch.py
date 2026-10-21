
import json
import subprocess
import sys


def main():
    try:
        hook_input = json.load(sys.stdin)
        cwd = hook_input.get("cwd", ".")

        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

        branch = result.stdout.strip()

        if branch == "main":
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "현재 브랜치가 main입니다. "
                        "코드 수정 전에 새 작업 브랜치를 만들어 주세요."
                    ),
                }
            }))
    except Exception as exc:
        # 브랜치를 확인할 수 없으면 안전하게 작업을 차단
        print(
            "브랜치를 확인하지 못했습니다: " + str(exc),
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
