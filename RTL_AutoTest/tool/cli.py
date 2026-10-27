"""명령줄 실행 (프로젝트 폴더에서)
  python tool/cli.py new      --ip MY_IP                 # IP 작업공간 생성
  python tool/cli.py extract  --ip VDDI-100              # 레지스터 정의 헤더(.vh) -> 02_regmap/regmap.yaml
  python tool/cli.py convert  --ip VDDI-100 --if i2c     # 테스트벡터 RTL -> 03_vectors/i2c/*.xml (Aardvark 배치, 툴 본 기능)
  python tool/cli.py demo     --ip VDDI-100 --if spi     # [For Demo] DUT RTL 시뮬레이션에 인가·판정
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_PYLIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pylibs")  # run_tool.py 의 대체 설치 위치
if os.path.isdir(_PYLIBS):
    sys.path.insert(0, _PYLIBS)

from core import workspace as ws  # noqa: E402
from core.pipeline import convert, extract_regmap, load_regmap, run_demo  # noqa: E402


def resolve_ip(s: str) -> str:
    return s if os.path.isdir(s) else os.path.join(ws.PROJECT_ROOT, s)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="RTL register/function auto test")
    ap.add_argument("cmd", choices=["new", "extract", "convert", "demo", "run"])
    ap.add_argument("--ip", default="VDDI-100", help="IP 이름 또는 경로")
    ap.add_argument("--if", dest="iface", choices=["spi", "i2c"], default="spi")
    ap.add_argument("--order", choices=["big", "little", "auto"], default="auto")
    ap.add_argument("--backend", choices=["sim", "model"], default="sim")
    ap.add_argument("--i2c-addr", type=lambda s: int(s, 16), default=None, help="hex, 예: 3C")
    a = ap.parse_args()

    if a.cmd == "new":
        print("생성:", ws.create_ip(a.ip))
        sys.exit(0)
    ip = resolve_ip(a.ip)
    if a.cmd == "extract":
        prev = load_regmap(ip) if os.path.exists(ws.p_regmap(ip)) else None
        rm, warns = extract_regmap(ip, None, prev)
        rm.validate()
        os.makedirs(os.path.dirname(ws.p_regmap(ip)), exist_ok=True)
        rm.save()
        print(f"{len(rm.regs)}개 레지스터 -> {os.path.relpath(rm.path, ip)}")
        for w in warns:
            print("  [확인] " + w)
    elif a.cmd == "convert":
        rm = load_regmap(ip)
        c = convert(ip, a.iface, a.order, a.i2c_addr if a.i2c_addr is not None else rm.i2c_addr)
        for p in c["files"]:
            print("  " + os.path.relpath(p, ip))
        print(f"{os.path.relpath(c['all'], ip)} (테스트벡터 {len(c['cases'])}개, 트랜잭션 {c['n_xfer']}개, {c['order']}-endian)")
        for w in c["warns"]:
            print("  [경고] " + w)
    else:
        r = run_demo(ip, a.iface, a.order, a.backend, a.i2c_addr)
        sys.exit(0 if all(x.passed for x in r["results"]) else 1)
