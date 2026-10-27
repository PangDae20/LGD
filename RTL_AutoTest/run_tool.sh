#!/bin/sh
# ==================================================================
#  RTL Test Vector -> SPI/I2C Converter  실행 (macOS / Linux)
#  실행 권한이 없으면:  sh run_tool.sh   또는   bash run_tool.sh
#   1) Python 3.9 이상 찾기 (tool/.venv -> python3 -> python -> python3.x)
#   2) 없으면 설치 방법 안내 (brew / apt)
#   3) tool/run_tool.py 로 나머지 점검(패키지, tkinter, iverilog) 후 GUI 실행
#  옵션: --check-only | --full | --yes | --cli
# ==================================================================
cd "$(dirname "$0")" || exit 1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

# macOS: 인터넷에서 받은 파일 격리 표시 해제 (실패해도 무시)
if [ "$(uname)" = "Darwin" ] && command -v xattr >/dev/null 2>&1; then
    xattr -dr com.apple.quarantine . 2>/dev/null
fi

echo "================================================================"
echo " Python 찾는 중..."
echo "================================================================"
PY=""
OLD=""
for c in tool/.venv/bin/python3 python3 python python3.13 python3.12 python3.11 python3.10 python3.9 \
         /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3; do
    if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
        "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2]>=(3,9) else 3)' >/dev/null 2>&1
        rc=$?
        if [ $rc -eq 0 ]; then PY="$c"; break; fi
        if [ $rc -eq 3 ]; then OLD="$("$c" -c 'import sys;print(sys.version.split()[0])' 2>/dev/null) ($c)"; fi
    fi
done

if [ -z "$PY" ]; then
    if [ -n "$OLD" ]; then echo "[FAIL] Python 버전이 낮음: $OLD (3.9 이상 필요)"
    else echo "[FAIL] 실행 가능한 Python 을 찾지 못함"; fi
    echo ""
    case "$(uname)" in
        Darwin) echo " 설치: brew install python python-tk   (또는 https://www.python.org/downloads/)";;
        Linux)  echo " 설치: sudo apt install python3 python3-venv python3-pip python3-tk   (Ubuntu/Debian)"
                echo "       sudo dnf install python3 python3-tkinter                      (Fedora/RHEL)";;
        *)      echo " 설치: https://www.python.org/downloads/";;
    esac
    exit 1
fi

echo "[ OK ] 사용할 Python: $PY ($("$PY" -c 'import sys;print(sys.version.split()[0])'))"
echo ""
"$PY" tool/run_tool.py "$@"
rc=$?
[ $rc -ne 0 ] && echo "" && echo "[FAIL] 점검 또는 실행 중 문제 발생 - tool/env_report.txt 확인"
exit $rc
