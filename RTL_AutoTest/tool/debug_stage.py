"""단계별 디버그 실행 — 한 단계만 돌려서 중간 결과를 눈으로 확인한다.

  [툴 본 기능]
  python tool/debug_stage.py extract  --ip VDDI-100                     1 헤더(.vh) 파싱: 레지스터·정의 줄·경고
  python tool/debug_stage.py regmap   --ip VDDI-100                     1 레지스터맵 검증 + 바이트 주소 배치
  python tool/debug_stage.py parse    --ip VDDI-100 [--test T03]        2 테스트벡터 RTL 파싱: 파일별 동작 수 / 지정 시험의 RTL 줄 -> 동작
  python tool/debug_stage.py convert  --ip VDDI-100 --if i2c --test T03 3 RTL 한 줄 -> SPI/I2C 줄 대응 확인
  [For Demo]
  python tool/debug_stage.py sim      --ip VDDI-100 --if spi --reg CHIP_ID   4 레지스터 하나를 DUT RTL에 인가해 바이트 확인
  python tool/debug_stage.py endian   --ip VDDI-100 --if spi            5 ID 레지스터 기반 엔디안 판단만
  python tool/debug_stage.py judge    --ip VDDI-100 [--order big]       5 판정 요약 (시험별 PASS/FAIL, 실패 항목)
  python tool/debug_stage.py golden   --ip VDDI-100 --scenario colorbar 5 기준 모델 vs DUT 프레임 비교 PNG 저장
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_PYLIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pylibs")  # run_tool.py 의 대체 설치 위치
if os.path.isdir(_PYLIBS):
    sys.path.insert(0, _PYLIBS)

from core import workspace as ws  # noqa: E402
from core.datatypes import Op, TestCase  # noqa: E402
from core.endian_detect import detect_byte_order  # noqa: E402
from core.judge import judge  # noqa: E402
from core.pipeline import load_cases, load_regmap, make_backend  # noqa: E402
from core.rtl_parser import extract  # noqa: E402
from core.tv_parser import count  # noqa: E402
from core.vector_cmd import serialize  # noqa: E402
from core.vector_export import export_with_map  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["extract", "regmap", "parse", "convert", "sim", "endian", "judge", "golden"])
    ap.add_argument("--ip", default="VDDI-100")
    ap.add_argument("--if", dest="iface", choices=["spi", "i2c"], default="spi")
    ap.add_argument("--order", choices=["big", "little", "auto"], default="auto")
    ap.add_argument("--backend", choices=["sim", "model"], default="sim")
    ap.add_argument("--test", default=None)
    ap.add_argument("--reg", default=None)
    ap.add_argument("--scenario", default="colorbar")
    ap.add_argument("--n", type=int, default=25)
    a = ap.parse_args()
    ip = a.ip if os.path.isdir(a.ip) else os.path.join(ws.PROJECT_ROOT, a.ip)

    if a.stage == "extract":
        files = ws.list_tv_headers(ip)
        hints, regs, warns = extract([os.path.join(ip, f) for f in files], base_dir=ip)
        print(f"[헤더] {len(files)}개: {', '.join(files)}")
        print(f"[힌트] {hints}")
        for r in regs:
            print(f"  0x{r['addr']:02X} {r['name']:11s} w={r['width']:2d} {r['access']} reset=0x{r['reset']:X} "
                  f"mask=0x{r['rw_mask']:X}  <- {r['src']}")
        for w in warns:
            print("  [확인]", w)
        return

    rm = load_regmap(ip)
    order = rm.spec_byte_order if a.order == "auto" else a.order
    addr = rm.i2c_addr

    if a.stage == "regmap":
        rm.validate()
        print(f"[검증 통과] {rm.name}: {len(rm.regs)}개, 사양서 순서={rm.spec_byte_order}, ID={rm.id_register}, "
              f"I2C=0x{addr:02X}, top={rm.ip.get('top')}")
        for r in rm.regs:
            lanes = ", ".join(f"0x{b:02X}->[{s + 7}:{s}]" for b, s in rm.byte_lanes(r, order))
            print(f"  {r.name:11s} {r.access} w={r.width:2d} reset=0x{r.reset:X} mask=0x{r.rw_mask:X}  ({order}) {lanes}")
    elif a.stage == "parse":
        cases, warns = load_cases(ip, rm)
        for tc in cases:
            print(f"  {tc.tid:4s} {tc.desc:22s} {tc.src_file:45s} {count(tc)}")
            if tc.tid == a.test:
                for op in tc.ops:
                    print(f"      {op.src.rsplit(':', 1)[-1]:>4s}: {op.text:55s} -> {op.kind} {op.reg or ''} "
                          f"value=0x{op.value:X} mask=0x{op.mask:X}")
        for w in warns:
            print("  [경고]", w)
    elif a.stage == "convert":
        cases, _ = load_cases(ip, rm)
        tc = next((c for c in cases if c.tid == (a.test or cases[0].tid)), cases[0])
        lines, srcs = export_with_map([tc], rm, order, a.iface, addr, header=False)
        rtl = {op.src: op.text for op in tc.ops}
        last = None
        for ln, src in zip(lines, srcs):
            if src and src != last:
                print(f"\n  RTL {src.rsplit(':', 1)[-1]:>4s}: {rtl.get(src, '')}")
                last = src
            if src:
                print(f"         -> {ln}")
            m = __import__("re").search(r"<!-- (\d{5}) ", ln)
            if a.n and m and int(m.group(1)) >= a.n:
                print("  ...")
                break
    elif a.stage == "sim":
        be = make_backend(a.backend, rm, ip, a.iface, addr)
        regs = [rm[a.reg]] if a.reg else rm.regs
        tc = TestCase("DBG", "debug", "debug", [Op("RST")] + [Op("RREG", r.name, r.reset, r.full_mask) for r in regs])
        cmd = serialize([tc], rm, order)
        print("[인가 명령]\n  " + "\n  ".join(c for c in cmd if not c.startswith("#")))
        raw = be.run(cmd, print)
        print("[읽은 바이트]")
        for a_, d, n in raw.reads:
            print(f"  0x{a_:02X} = 0x{d:02X}" + ("  NACK" if n else ""))
        for res in judge([tc], rm, order, raw):
            print(f"  {res.item:20s} 기대 {res.expected} 실측 {res.actual} {'PASS' if res.passed else 'FAIL'} {res.note}")
        if hasattr(be, "workdir"):
            print(f"[원본 파일] {be.workdir}")
    elif a.stage == "endian":
        be = make_backend(a.backend, rm, ip, a.iface, addr)
        print(detect_byte_order(be, rm, print))
    elif a.stage == "judge":
        from core.pipeline import run_demo
        r = run_demo(ip, a.iface, a.order, a.backend, addr, log=lambda m: None)
        from collections import Counter
        c = Counter((x.tid, x.passed) for x in r["results"])
        for tid in sorted({x.tid for x in r["results"]}):
            print(f"  {tid}: PASS {c[(tid, True)]}  FAIL {c[(tid, False)]}")
        for x in r["results"]:
            if not x.passed:
                print(f"  FAIL {x.tid} {x.item:24s} 기대 {x.expected} 실측 {x.actual} {x.note}")
        print(f"[리포트] {r['report']}")
    elif a.stage == "golden":
        from core.report import frame_images
        cases, _ = load_cases(ip, rm)
        tc = next(t for t in cases if any(op.kind == "FRAME" for op in t.ops))
        i = [op.label for op in tc.ops if op.kind == "FRAME"].index(a.scenario)
        start = [k for k, op in enumerate(tc.ops) if op.kind == "RST"][i]
        end = [k for k, op in enumerate(tc.ops) if op.kind == "FRAME"][i]
        one = TestCase(tc.tid, tc.ttype, tc.desc, tc.ops[start:end + 1])
        be = make_backend(a.backend, rm, ip, a.iface, addr)
        o = detect_byte_order(be, rm, lambda m: None)[0] if a.order == "auto" else order
        res = judge([one], rm, o, be.run(serialize([one], rm, o), print))[0]
        out = os.path.join(ip, ".work", f"golden_{a.scenario}")
        for name, im in zip(("expected", "captured", "diff"), frame_images(res.frame)):
            im.save(f"{out}_{name}.png")
        print(f"{a.scenario}: {'PASS' if res.passed else 'FAIL'} {res.note} -> {out}_*.png")


if __name__ == "__main__":
    main()
