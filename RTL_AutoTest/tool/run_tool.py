"""실행 환경 점검 + 자동 준비 + 실행 런처 (처음 보는 PC용).

점검 항목
  1  Python 버전 / 비트 / 실행 파일 위치
  2  프로젝트 폴더 쓰기 권한 (결과 파일 저장 위치)
  3  필수 파일, 스크립트 문법 호환성
  4  tkinter (GUI)
  5  pip, 필수 패키지 (pyyaml, pillow)
     -> 없으면 설치: 프로젝트 전용 가상환경(tool/.venv) 생성 후 설치 (관리자 권한 불필요)
        가상환경 실패 시 --user 설치, 그것도 막히면 tool/_pylibs 폴더에 설치
  6  패키지 서버(PyPI) 연결 (설치가 필요할 때만)
  7  [For Demo] iverilog (동봉판 -> PATH -> 기본 설치 경로), DUT RTL 컴파일
  8  자가 점검 18항목 (--full)

사용
  python tool/run_tool.py               점검 -> (필요 시 설치) -> GUI
  python tool/run_tool.py --check-only  점검만
  python tool/run_tool.py --full        점검 + 자가 점검(self_check) -> GUI
  python tool/run_tool.py --yes         설치 여부를 묻지 않고 진행
  python tool/run_tool.py --cli         GUI 대신 명령줄 변환
결과는 tool/env_report.txt 에 저장.
"""
# 이 파일은 오래된 Python에서도 "버전이 낮다"는 안내를 보여줄 수 있게 3.6 문법까지만 사용
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))          # tool/
PROJECT = os.path.dirname(ROOT)
MIN_PY = (3, 9)
TESTED_PY = [(3, 9), (3, 10), (3, 11), (3, 12), (3, 13)]
REQUIREMENTS = os.path.join(ROOT, "requirements.txt")
VENV_DIR = os.path.join(ROOT, ".venv")
PYLIBS = os.path.join(ROOT, "_pylibs")
SCRIPT_DIRS = [ROOT, os.path.join(ROOT, "core"), os.path.join(ROOT, "gui")]
REQUIRED_FILES = ["config/test_template.yaml", "tb/tb_harness.v", "tb/spi_master.vh", "tb/i2c_master.vh",
                  "run_gui.py", "cli.py", "requirements.txt"]
IMPORT_NAME = {"pyyaml": "yaml", "pillow": "PIL"}

# 콘솔 인코딩 (Windows cp949 콘솔에서 한글 출력 오류 방지)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if os.path.isdir(PYLIBS) and PYLIBS not in sys.path:
    sys.path.insert(0, PYLIBS)

report = []
summary = []


def say(status, msg):
    mark = {"OK": "[ OK ]", "WARN": "[WARN]", "FAIL": "[FAIL]", "INFO": "[INFO]", "FIX": "[FIX ]"}[status]
    line = "{} {}".format(mark, msg)
    print(line)
    report.append(line)


def item(name, status, detail=""):
    summary.append((name, status, detail))


def ask(msg, auto_yes):
    if auto_yes:
        print(msg + " [자동: y]")
        return True
    try:
        return input(msg + " [Y/n] ").strip().lower() in ("", "y", "yes")
    except EOFError:
        return True


def run(cmd, timeout=None):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=timeout)
        return p.returncode, p.stdout
    except Exception as e:  # noqa
        return -1, str(e)


def in_venv():
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix


def venv_python():
    for rel in (("Scripts", "python.exe"), ("bin", "python3"), ("bin", "python")):
        p = os.path.join(VENV_DIR, *rel)
        if os.path.exists(p):
            return p
    return None


def vtuple(s):
    out = []
    for p in s.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        if not num:
            break
        out.append(int(num))
    return tuple(out)


def read_requirements():
    reqs = []
    with open(REQUIREMENTS, encoding="utf-8") as f:
        for ln in f:
            ln = ln.split("#", 1)[0].strip()
            if ln:
                name, _, ver = ln.partition(">=")
                reqs.append((name.strip(), (ver or "0").strip()))
    return reqs


def installed_version(dist):
    try:
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:
        return None
    try:
        return version(dist)
    except PackageNotFoundError:
        mod = IMPORT_NAME.get(dist.lower(), dist)
        try:
            m = __import__(mod)
            return getattr(m, "__version__", "0")
        except Exception:
            return None


# ---------------------------------------------------------------------- 1
def check_python():
    v = sys.version_info[:3]
    vs = ".".join(map(str, v))
    bits = platform.architecture()[0]
    say("INFO", "Python {} {} ({}){} / {} {}".format(vs, bits, sys.executable, " [가상환경]" if in_venv() else "",
                                                     platform.system(), platform.release()))
    if v[:2] < MIN_PY:
        say("FAIL", "Python {}.{} 이상 필요 (현재 {}) -> https://www.python.org/downloads/ 에서 3.12 설치"
            .format(MIN_PY[0], MIN_PY[1], vs))
        item("Python", "FAIL", vs)
        return False
    if bits.startswith("32"):
        say("WARN", "32비트 Python -> 일부 패키지 설치가 느리거나 실패할 수 있음 (64비트 권장)")
    if tuple(v[:2]) not in TESTED_PY:
        say("WARN", "검증 범위(3.9~3.13) 밖의 버전 -> 동작은 할 가능성이 높지만 검증 안 됨")
        item("Python", "WARN", vs)
    else:
        say("OK", "Python 버전 {}".format(vs))
        item("Python", "OK", vs)
    return True


# ---------------------------------------------------------------------- 2
def check_write():
    test = os.path.join(PROJECT, ".write_test")
    try:
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        say("OK", "프로젝트 폴더 쓰기 가능 ({})".format(PROJECT))
        item("쓰기 권한", "OK")
        return True
    except Exception as e:
        say("FAIL", "프로젝트 폴더에 쓸 수 없음 ({}) -> 폴더를 바탕화면 등 쓰기 가능한 곳으로 복사 후 실행".format(e))
        item("쓰기 권한", "FAIL", "폴더 복사 필요")
        return False


# ---------------------------------------------------------------------- 3
def check_files():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        for f in missing:
            say("FAIL", "필수 파일 없음: tool/{}".format(f))
        say("INFO", "압축을 '모두 풀기'로 전부 해제했는지 확인 (압축 파일 안에서 바로 실행하면 안 됨)")
        item("필수 파일", "FAIL", ", ".join(missing))
        return False
    bad, n = [], 0
    for d in SCRIPT_DIRS:
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".py"):
                n += 1
                path = os.path.join(d, fn)
                try:
                    with open(path, encoding="utf-8") as f:
                        compile(f.read(), path, "exec")
                except SyntaxError as e:
                    bad.append("{} line {}: {}".format(fn, e.lineno, e.msg))
    if bad:
        for b in bad:
            say("FAIL", "현재 Python에서 문법 오류: " + b)
        item("스크립트", "FAIL", bad[0])
        return False
    say("OK", "필수 파일 {}개, 스크립트 {}개 컴파일 가능".format(len(REQUIRED_FILES), n))
    item("필수 파일/스크립트", "OK")
    return True


# ---------------------------------------------------------------------- 4
def check_tk():
    try:
        import tkinter
        r = tkinter.Tcl().eval("info patchlevel")
        say("OK", "tkinter (Tcl/Tk {})".format(r))
        item("tkinter(GUI)", "OK", r)
        return True
    except Exception as e:
        hint = {"Windows": "python.org 설치 파일로 다시 설치 (설치 옵션에서 'tcl/tk and IDLE' 체크)",
                "Darwin": "brew install python-tk 또는 python.org 설치본 사용",
                "Linux": "sudo apt install python3-tk (Ubuntu/Debian)"}.get(platform.system(), "")
        say("WARN", "tkinter 사용 불가: {} -> {}. GUI 없이 명령줄(--cli)로는 실행 가능".format(e, hint))
        item("tkinter(GUI)", "WARN", "명령줄만 가능")
        return False


# ---------------------------------------------------------------------- 5, 6
def missing_packages():
    need = []
    for dist, minv in read_requirements():
        cur = installed_version(dist)
        if cur is None:
            say("WARN", "{} 미설치 (필요 >= {})".format(dist, minv))
            need.append("{}>={}".format(dist, minv))
        elif vtuple(cur) < vtuple(minv):
            say("WARN", "{} {} -> 버전 낮음 (필요 >= {})".format(dist, cur, minv))
            need.append("{}>={}".format(dist, minv))
        else:
            say("OK", "{} {}".format(dist, cur))
    return need


def check_network():
    try:
        import urllib.request
        urllib.request.urlopen("https://pypi.org/simple/pip/", timeout=6)
        say("OK", "패키지 서버(PyPI) 연결 가능")
        return True
    except Exception as e:
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        say("WARN", "PyPI 연결 실패 ({}){} -> 네트워크/프록시 확인. 설치 없이 실행 가능한지 계속 진행"
            .format(e, " / 프록시: " + proxy if proxy else ""))
        return False


def ensure_pip(py):
    code, out = run([py, "-m", "pip", "--version"], 60)
    if code == 0:
        return True
    say("FIX", "pip 없음 -> ensurepip 로 설치 시도")
    code, out = run([py, "-m", "ensurepip", "--upgrade"], 300)
    if code == 0:
        return True
    say("FAIL", "pip 설치 실패: " + out.strip()[-200:])
    return False


def pip_install(py, need, extra):
    cmd = [py, "-m", "pip", "install", "--disable-pip-version-check"] + extra + need
    say("FIX", "실행: " + " ".join(cmd))
    code, out = run(cmd, 900)
    tail = "\n".join(out.strip().splitlines()[-3:])
    if code != 0:
        say("WARN", "설치 실패:\n" + tail)
    return code == 0


def relaunch(py, args):
    say("INFO", "가상환경 Python으로 다시 점검: " + py)
    sys.stdout.flush()
    code = subprocess.call([py, os.path.abspath(__file__)] + args + ["--relaunched"])
    sys.exit(code)


def check_packages(args, auto_yes):
    need = missing_packages()
    if not need:
        item("패키지", "OK")
        return True
    if not ask("\n누락/구버전 패키지: {}\n설치할까요? (관리자 권한 필요 없음)".format(" ".join(need)), auto_yes):
        say("FAIL", "패키지 미설치 -> 실행 불가")
        item("패키지", "FAIL", " ".join(need))
        return False
    check_network()

    # 1) 이미 가상환경 안이면 그대로 설치
    if in_venv():
        if ensure_pip(sys.executable) and pip_install(sys.executable, need, []):
            return _recheck()
    # 2) 프로젝트 전용 가상환경 만들기
    elif "--relaunched" not in args:
        vpy = venv_python()
        if not vpy:
            say("FIX", "프로젝트 전용 가상환경 생성: tool/.venv")
            code, out = run([sys.executable, "-m", "venv", VENV_DIR], 300)
            vpy = venv_python() if code == 0 else None
            if not vpy:
                say("WARN", "가상환경 생성 실패 (" + out.strip()[-150:] + ")")
        allreq = ["{}>={}".format(d, v) for d, v in read_requirements()]   # 새 가상환경엔 전부 설치
        if vpy and ensure_pip(vpy) and pip_install(vpy, allreq, []):
            relaunch(vpy, [a for a in args if a != "--relaunched"])
    # 3) 사용자 영역 설치
    if ensure_pip(sys.executable):
        if pip_install(sys.executable, need, ["--user"]):
            return _recheck()
        # 4) tool/_pylibs 에 설치 (시스템 정책으로 --user 도 막힌 경우)
        if pip_install(sys.executable, need, ["--target", PYLIBS, "--upgrade"]):
            if PYLIBS not in sys.path:
                sys.path.insert(0, PYLIBS)
            return _recheck()
    say("FAIL", "모든 설치 방법 실패 -> 인터넷 연결 확인 후 다시 실행, 또는 담당자에게 'pip install pyyaml pillow' 요청")
    item("패키지", "FAIL", " ".join(need))
    return False


def _recheck():
    import importlib
    importlib.invalidate_caches()
    if os.path.isdir(PYLIBS) and PYLIBS not in sys.path:
        sys.path.insert(0, PYLIBS)
    left = [d for d, _ in read_requirements() if installed_version(d) is None]
    if left:
        say("FAIL", "설치 후에도 찾을 수 없음: " + ", ".join(left))
        item("패키지", "FAIL", ", ".join(left))
        return False
    say("OK", "패키지 설치 완료")
    item("패키지", "OK", "설치함")
    return True


# ---------------------------------------------------------------------- 7
def check_iverilog():
    sys.path.insert(0, ROOT)
    from core.sim_runner import BUNDLED_BIN, HARNESS, TB_DIR, locate_iverilog
    from core.workspace import list_dut, list_ips
    t = locate_iverilog()
    if not t:
        say("WARN", "iverilog 없음 -> [For Demo]는 'Python 모델'로 실행 (변환 기능은 영향 없음)")
        say("INFO", "RTL 시뮬레이션까지 쓰려면: {} 에 포터블판 또는 https://bleyer.org/icarus/ 설치"
            .format(os.path.relpath(BUNDLED_BIN, PROJECT)))
        item("iverilog(Demo)", "WARN", "Python 모델로 대체")
        return
    code, out = run([t[0], "-V"], 20)
    if code != 0 or not out:
        say("WARN", "iverilog 실행 실패 ({}: {}) -> 보안 프로그램 차단 확인. Python 모델로 실행 가능".format(t[2], out[:120]))
        item("iverilog(Demo)", "WARN", "실행 차단")
        return
    ver = out.splitlines()[0]
    say("OK", "iverilog: {} / 출처: {}".format(ver, t[2]))
    ok_all = True
    for ip in list_ips():
        files = [os.path.join(ip, f) for f in list_dut(ip) if not f.endswith((".vh", ".svh"))]
        if not files:
            continue
        outp = os.path.join(ip, ".work", "env_check.vvp")
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        code, msg = run([t[0], "-g2005", "-I" + TB_DIR, "-o", outp, HARNESS] + files, 120)
        if code == 0:
            say("OK", "[For Demo] {} DUT RTL 컴파일".format(os.path.basename(ip)))
        else:
            ok_all = False
            say("WARN", "{} RTL 컴파일 실패: {}".format(os.path.basename(ip), msg.strip()[:200]))
    item("iverilog(Demo)", "OK" if ok_all else "WARN", t[2])


# ---------------------------------------------------------------------- 8
def run_self_check():
    code, out = run([sys.executable, os.path.join(ROOT, "self_check.py")], 300)
    last = [ln for ln in out.strip().splitlines() if ln.strip()][-1:] or ["(출력 없음)"]
    if code == 0:
        say("OK", "자가 점검: " + last[0])
        item("자가 점검", "OK", last[0])
    else:
        for ln in out.splitlines():
            if "[FAIL]" in ln or "확인할 곳" in ln:
                say("WARN", ln.strip())
        item("자가 점검", "WARN", last[0])


def print_summary():
    print("\n" + "=" * 64 + "\n 요약")
    print("-" * 64)
    for name, st, detail in summary:
        print(" {:<20s} {:<5s} {}".format(name, st, detail))
    print("=" * 64)


def main():
    args = sys.argv[1:]
    auto_yes = "--yes" in args
    print("=" * 64 + "\n RTL Test Vector -> SPI/I2C Converter — 실행 환경 점검\n" + "=" * 64)
    ok = check_python()
    ok = ok and check_write()
    ok = ok and check_files()
    has_tk = check_tk() if ok else False
    ok = ok and check_packages(args, auto_yes)
    if ok:
        check_iverilog()
        if "--full" in args or "--check-only" in args:
            run_self_check()
    print_summary()
    try:
        with open(os.path.join(ROOT, "env_report.txt"), "w", encoding="utf-8") as f:
            f.write("# 환경 점검 {:%Y-%m-%d %H:%M:%S}\n".format(datetime.now()) + "\n".join(report) + "\n")
    except Exception:
        pass
    if not ok:
        print("환경 문제로 종료. 위 [FAIL] 항목과 tool/env_report.txt 확인")
        sys.exit(1)
    if "--check-only" in args:
        print("점검 완료 (--check-only)")
        return
    if "--cli" in args or not has_tk:
        print("명령줄 변환 실행 (VDDI-100, SPI)")
        subprocess.call([sys.executable, os.path.join(ROOT, "cli.py"), "convert"])
        return
    print("GUI 실행")
    sys.stdout.flush()
    subprocess.call([sys.executable, os.path.join(ROOT, "run_gui.py")], cwd=ROOT)


if __name__ == "__main__":
    main()
