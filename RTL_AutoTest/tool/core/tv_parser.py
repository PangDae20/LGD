"""[2단계] 테스트벡터 RTL -> 레지스터 단위 동작 (TestCase / Op).

테스트벡터 RTL 형식 (01_input/testvector/tv_*.v, tv_tasks.vh 의 태스크 사용)
  // @test T03 RW 패턴 쓰기/읽기         <- 시험 ID와 설명 (없으면 파일 이름)
  chip_reset;                            <- 칩 리셋
  reg_write(ADDR_H_ACTIVE, 16'h0040);    <- 레지스터 쓰기 (레지스터 폭 단위 값)
  reg_read (ADDR_H_ACTIVE, 16'h0040, 16'h07FF);   // 주석은 항목 이름으로 사용
                                          <- 레지스터 읽기 (기대값, 비교 마스크; 마스크 생략 시 전체 비트)
  frame_check("colorbar");               <- 화면 1프레임 캡처·비교 (데모 DUT 전용)

주소는 ADDR_<레지스터 이름> 기호 또는 숫자(7'h04) 모두 가능. 레지스터 폭·바이트 순서는 레지스터맵에서 가져온다.
"""
import os
import re
from typing import Dict, List, Optional, Tuple

from .datatypes import Op, TestCase
from .regmap import RegMap

RE_TEST = re.compile(r"//\s*@test\s+(\S+)\s*(.*)")
RE_RESET = re.compile(r"^\s*chip_reset\s*(\(\s*\))?\s*;")
RE_WRITE = re.compile(r"^\s*reg_write\s*\(\s*([^,]+?)\s*,\s*([^,)]+?)\s*\)\s*;")
RE_READ = re.compile(r"^\s*reg_read\s*\(\s*([^,]+?)\s*,\s*([^,)]+?)\s*(?:,\s*([^,)]+?)\s*)?\)\s*;")
RE_FRAME = re.compile(r'^\s*frame_check\s*\(\s*"([^"]+)"\s*\)\s*;')
RE_VNUM = re.compile(r"^(\d+)?\s*'\s*[sS]?([hHdDbBoO])\s*([0-9a-fA-F_]+)$")


def parse_number(s: str) -> int:
    """Verilog 숫자 (16'h0040, 'hFF, 8'b1010, 96, 0x40) -> int"""
    s = s.strip()
    m = RE_VNUM.match(s)
    if m:
        base = {"h": 16, "d": 10, "b": 2, "o": 8}[m.group(2).lower()]
        return int(m.group(3).replace("_", ""), base)
    return int(s.replace("_", ""), 0)


def _resolve(rm: RegMap, expr: str):
    expr = expr.strip()
    if expr.startswith("ADDR_"):
        name = expr[5:]
        try:
            return rm[name]
        except KeyError:
            raise ValueError(f"레지스터맵에 없는 레지스터: {expr}")
    a = parse_number(expr)
    for r in rm.regs:
        if r.addr == a:
            return r
    raise ValueError(f"레지스터맵에 없는 주소: {expr}")


def parse_file(path: str, rm: RegMap, rel: str = None) -> Tuple[Optional[TestCase], List[str]]:
    rel = rel or os.path.basename(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    warns: List[str] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    tc = TestCase(stem, stem, stem, src_file=rel)
    state: Dict[str, int] = {r.name: r.reset for r in rm.regs}
    for no, raw in enumerate(lines, 1):
        m = RE_TEST.search(raw)
        if m:
            tc.tid, tc.desc = m.group(1), m.group(2).strip() or stem
            continue
        code, _, cmt = raw.partition("//")
        label = cmt.strip()
        src = f"{rel}:{no}"
        stmt = code.strip()
        if not stmt:
            continue
        try:
            if RE_RESET.match(code):
                tc.ops.append(Op("RST", src=src, text=stmt))
                state = {r.name: r.reset for r in rm.regs}
            elif RE_WRITE.match(code):
                g = RE_WRITE.match(code)
                r = _resolve(rm, g.group(1))
                v = parse_number(g.group(2))
                if v > r.full_mask:
                    warns.append(f"{src}: 값 0x{v:X} 가 {r.name}({r.width}비트) 보다 큼 -> 하위 비트만 사용")
                    v &= r.full_mask
                tc.ops.append(Op("WREG", r.name, v, label=label, src=src, text=stmt))
                if r.access == "RW":
                    state[r.name] = (state[r.name] & ~r.rw_mask) | (v & r.rw_mask)
            elif RE_READ.match(code):
                g = RE_READ.match(code)
                r = _resolve(rm, g.group(1))
                exp = parse_number(g.group(2)) & r.full_mask
                mask = parse_number(g.group(3)) & r.full_mask if g.group(3) else r.full_mask
                tc.ops.append(Op("RREG", r.name, exp, mask, label, src=src, text=stmt))
            elif RE_FRAME.match(code):
                name = RE_FRAME.match(code).group(1)
                tc.ops.append(Op("FRAME", label=name, golden=dict(state), src=src, text=stmt))
            elif re.search(r"\b(reg_write|reg_read|frame_check|chip_reset)\b", code):
                warns.append(f"{src}: 형식을 해석하지 못함 -> {stmt}")
        except ValueError as e:
            warns.append(f"{src}: {e}")
    if not tc.ops:
        warns.append(f"{rel}: 레지스터 동작이 없음")
        return None, warns
    return tc, warns


def parse(files: List[str], rm: RegMap, base_dir: str = None) -> Tuple[List[TestCase], List[str]]:
    cases, warns = [], []
    for p in files:
        rel = os.path.relpath(p, base_dir).replace("\\", "/") if base_dir else None
        tc, w = parse_file(p, rm, rel)
        warns += w
        if tc:
            cases.append(tc)
    return cases, warns


def count(tc: TestCase) -> Dict[str, int]:
    k: Dict[str, int] = {}
    for op in tc.ops:
        k[op.kind] = k.get(op.kind, 0) + 1
    return k


if __name__ == "__main__":
    # 디버그: python -m core.tv_parser <regmap.yaml> <tv_*.v ...>
    import sys
    rm = RegMap.load(sys.argv[1])
    cases, warns = parse(sys.argv[2:], rm)
    for tc in cases:
        print(f"{tc.tid} {tc.desc} ({tc.src_file}) {count(tc)}")
        for op in tc.ops[:12]:
            print(f"   {op.src:28s} {op.kind:5s} {op.reg or '':11s} 0x{op.value:X} mask=0x{op.mask:X}  {op.text}")
    for w in warns:
        print("[경고]", w)
