"""GUI 실행 진입점 (보통은 run_tool.py 가 환경 점검 후 이 파일을 실행)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_PYLIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pylibs")  # run_tool.py 의 대체 설치 위치
if os.path.isdir(_PYLIBS):
    sys.path.insert(0, _PYLIBS)

from gui.app import App  # noqa: E402

if __name__ == "__main__":
    App().mainloop()
