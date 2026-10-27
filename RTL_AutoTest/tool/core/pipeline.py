"""전체 흐름

[툴 본 기능]  테스트벡터 RTL -> SPI / I2C 포맷 변환
  1 레지스터맵   헤더(*.vh)에서 추출 -> 검토 -> 저장      extract_regmap / load_regmap
  2 파싱         테스트벡터 RTL -> 레지스터 단위 동작       load_cases
  3 변환         -> SPI / I2C 포맷 파일 (03_vectors)       convert

[For Demo]  실물 칩 + SPI/I2C 장비 대신 DUT RTL 시뮬레이션으로 인가·판정
  4 인가 / 5 판정 / 6 리포트                               run_demo
"""
import os
import shutil
from datetime import datetime
from typing import Callable, List, Optional

from . import workspace as ws
from .datatypes import RawResult
from .endian_detect import detect_byte_order
from .judge import judge
from .model_runner import ModelBackend
from .regmap import RegMap, Register
from .report import write_reports
from .rtl_parser import extract
from .sim_runner import SimBackend
from .tv_parser import parse
from .vector_cmd import count_xfers, serialize
from .vector_export import export_with_map


# ------------------------------------------------------------------ 1 레지스터맵
def extract_regmap(ip: str, files: Optional[List[str]] = None, prev: Optional[RegMap] = None):
    """레지스터 정의 헤더(기본: 01_input/testvector/*.vh)에서 레지스터맵 초안 추출.
    이전 regmap에서 사람이 정한 값(byte_order 등)은 유지."""
    files = files or ws.list_tv_headers(ip)
    hints, regs, warns = extract([os.path.join(ip, f) for f in files], base_dir=ip)
    meta = dict(prev.ip) if prev else {}
    meta.setdefault("name", os.path.basename(os.path.abspath(ip)))
    meta["source_files"] = list(files)
    if "i2c_addr" in hints:
        meta["i2c_addr"] = hints["i2c_addr"]
    meta.setdefault("byte_order", "big")
    meta["reg_src"] = {r["name"]: r["src"] for r in regs}
    objs = [Register(**{k: v for k, v in r.items() if k != "src"}) for r in regs]
    if not meta.get("id_register") or meta["id_register"] not in {r.name for r in objs}:
        cand = [r.name for r in objs if r.access == "RO" and "ID" in r.name and r.reset]
        meta["id_register"] = cand[0] if cand else (objs[0].name if objs else "")
    for k in ("top", "rtl_files", "rtl_byte_order_hint"):
        meta.pop(k, None)
    return RegMap(meta, objs, ws.p_regmap(ip)), warns


def load_regmap(ip: str) -> RegMap:
    return RegMap.load(ws.p_regmap(ip))


# ------------------------------------------------------------------ 2 파싱
def load_cases(ip: str, rm: RegMap, files: Optional[List[str]] = None):
    files = files if files is not None else ws.list_tv(ip)
    return parse([os.path.join(ip, f) for f in files], rm, base_dir=ip)


# ------------------------------------------------------------------ 3 변환
def convert(ip: str, iface: str, order: str, i2c_addr: int, files: Optional[List[str]] = None,
            rm: Optional[RegMap] = None, outdir: Optional[str] = None):
    """테스트벡터 RTL -> 03_vectors/<iface>/<파일>_<iface>.xml + all_<iface>.xml (Aardvark 배치)
    outdir 를 주면 그 폴더에 쓴다 (For Demo 는 04_results/<실행>/vectors 에 써서 03_vectors 를 건드리지 않음)"""
    rm = rm or load_regmap(ip)
    if order == "auto":
        order = rm.spec_byte_order
    if files is not None and not files:
        raise ValueError("'사용' 표시된 테스트벡터 RTL이 없습니다")
    cases, warns = load_cases(ip, rm, files)
    if not cases:
        raise ValueError("변환할 테스트벡터가 없습니다 (레지스터 동작 없음)")
    outdir = outdir or ws.p_vectors(ip, iface)
    os.makedirs(outdir, exist_ok=True)
    written = []
    for tc in cases:
        lines, _ = export_with_map([tc], rm, order, iface, i2c_addr)
        stem = os.path.splitext(os.path.basename(tc.src_file))[0]
        p = os.path.join(outdir, f"{stem}_{iface}.xml")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        written.append(p)
    all_lines, _ = export_with_map(cases, rm, order, iface, i2c_addr)
    all_path = os.path.join(outdir, f"all_{iface}.xml")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines) + "\n")
    cmd = serialize(cases, rm, order)
    return {"files": written, "all": all_path, "lines": all_lines, "cmd": cmd, "cases": cases,
            "warns": warns, "order": order, "n_xfer": count_xfers(cmd)}


# ================================================================== For Demo
def demo_top(ip: str) -> str:
    h, _, _ = extract([os.path.join(ip, f) for f in ws.list_dut(ip)], ip)
    return h.get("top", "top")


def dut_byte_order_hint(ip: str) -> Optional[str]:
    h, _, _ = extract([os.path.join(ip, f) for f in ws.list_dut(ip)], ip)
    return h.get("rtl_byte_order")


def make_backend(kind: str, rm: RegMap, ip: str, iface: str, i2c_addr: int):
    """[For Demo] 실물 칩 대신 인가할 대상"""
    if kind == "sim":
        files = [os.path.join(ip, f) for f in ws.list_dut(ip) if not f.endswith((".vh", ".svh"))]
        if not files:
            raise RuntimeError(f"{ws.DEMO_DUT} 에 DUT RTL이 없습니다")
        return SimBackend(files, demo_top(ip), iface, i2c_addr, ws.p_work(ip, iface))
    little = (dut_byte_order_hint(ip) or rm.spec_byte_order) == "little"
    return ModelBackend(rm, little)


def _save_debug(dbg: str, cmd: List[str], raw: RawResult, be, info: dict):
    os.makedirs(dbg, exist_ok=True)
    with open(os.path.join(dbg, "cmd_vectors.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(cmd) + "\n")
    with open(os.path.join(dbg, "raw_reads.csv"), "w", encoding="utf-8") as f:
        f.write("idx,addr,data,nack\n")
        for i, (a, d, n) in enumerate(raw.reads):
            f.write(f"{i},0x{a:02X},0x{d:02X},{int(n)}\n")
    if isinstance(be, SimBackend):
        for fn in ("sim_log.txt", "compile.log"):
            src = os.path.join(be.workdir, fn)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dbg, fn))
    with open(os.path.join(dbg, "run_info.txt"), "w", encoding="utf-8") as f:
        for k, v in info.items():
            f.write(f"{k}: {v}\n")


def run_demo(ip: str, iface: str = "spi", order: str = "auto", backend: str = "sim",
             i2c_addr: Optional[int] = None, files: Optional[List[str]] = None,
             log: Callable[[str], None] = print):
    """[For Demo] 변환한 테스트벡터를 DUT RTL 시뮬레이션에 인가하고 판정"""
    rm = load_regmap(ip)
    i2c_addr = rm.i2c_addr if i2c_addr is None else i2c_addr
    be = make_backend(backend, rm, ip, iface, i2c_addr)
    log(f"[For Demo] IP: {rm.name} / {iface.upper()}" + (f" (장치 주소 0x{i2c_addr:02X})" if iface == "i2c" else "")
        + f" / 인가 대상: {be.name}")

    detect_msg = ""
    if order == "auto":
        order, detect_msg = detect_byte_order(be, rm, log)
        log("[엔디안 자동 감지] " + detect_msg)
    else:
        log(f"바이트 순서 고정: {order}")

    base = os.path.join(ws.p_results(ip), datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{iface}_{order}")
    outdir, k = base, 1
    while os.path.exists(outdir):
        k += 1
        outdir = f"{base}_{k}"
    cv = convert(ip, iface, order, i2c_addr, files, rm, outdir=os.path.join(outdir, "vectors"))
    for w in cv["warns"]:
        log("[테스트벡터 경고] " + w)
    log(f"변환: 테스트벡터 RTL {len(cv['cases'])}개 -> {os.path.relpath(cv['all'], ip)} (트랜잭션 {cv['n_xfer']}개)")
    raw = be.run(cv["cmd"], log)
    results = judge(cv["cases"], rm, order, raw, ws.load_overrides(ip), ip)
    npass = sum(r.passed for r in results)
    log(f"판정 완료: {npass}/{len(results)} PASS")

    meta = {"IP": rm.name, "인터페이스": iface.upper(), "인가 대상 (For Demo)": be.name,
            "사양서 바이트 순서": rm.spec_byte_order, "적용 바이트 순서": order,
            "테스트벡터 RTL": f"{len(cv['cases'])}개 ({ws.INPUT_TV})",
            "변환 결과": os.path.relpath(cv["all"], ip).replace("\\", "/")}
    if iface == "i2c":
        meta["I2C 장치 주소"] = f"0x{i2c_addr:02X}"
    if detect_msg:
        meta["엔디안 자동 감지"] = detect_msg
    report = write_reports(results, outdir, meta)
    _save_debug(os.path.join(outdir, "debug"), cv["cmd"], raw, be, {**meta, "PASS": f"{npass}/{len(results)}"})
    log(f"리포트: {os.path.relpath(report, ip)}")
    return {"order": order, "detect": detect_msg, "cases": cv["cases"], "vectors": cv["lines"],
            "vector_path": cv["all"], "results": results, "report": report, "regmap": rm, "outdir": outdir}


run_all = run_demo   # 이전 이름 호환
