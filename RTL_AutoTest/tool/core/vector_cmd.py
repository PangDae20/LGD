"""[3단계] 레지스터 단위 동작 -> 바이트 단위 명령 (인터페이스 공통 중간 형식).

명령 (데모 하네스 tool/tb/tb_harness.v 도 이 형식을 읽음)
  RST            리셋
  W <addr> <data>   1바이트 쓰기 (hex)
  R <addr>          1바이트 읽기 (hex)
  F              화면 1프레임 캡처
16비트 이상 레지스터는 바이트 순서(order)에 따라 바이트 주소로 펼친다.
"""
from typing import Iterator, List, Tuple

from .datatypes import TestCase
from .regmap import RegMap


def expand(cases: List[TestCase], rm: RegMap, order: str) -> Iterator[Tuple[str, tuple, str, str]]:
    """(명령, 인자, 주석, 테스트벡터 RTL 위치) 단위로 펼침"""
    for tc in cases:
        yield "#", (), f"{tc.tid} {tc.desc}  <- {tc.src_file}", tc.src_file
        for op in tc.ops:
            if op.kind == "RST":
                yield "RST", (), "", op.src
            elif op.kind == "WREG":
                for a, d in rm.split(rm[op.reg], op.value, order):
                    yield "W", (a, d), op.reg, op.src
            elif op.kind == "RREG":
                reg = rm[op.reg]
                exp = dict(rm.split(reg, op.value, order))
                msk = dict(rm.split(reg, op.mask, order))
                for a, _ in rm.byte_lanes(reg, order):
                    yield "R", (a, exp[a], msk[a]), f"{op.reg} {op.label}".strip(), op.src
            elif op.kind == "FRAME":
                yield "F", (), op.label, op.src


def serialize(cases: List[TestCase], rm: RegMap, order: str) -> List[str]:
    lines = []
    for cmd, args, note, _ in expand(cases, rm, order):
        if cmd == "#":
            lines.append(f"# {note}")
        elif cmd == "RST":
            lines.append("RST")
        elif cmd == "W":
            lines.append(f"W {args[0]:02X} {args[1]:02X}    # {note}")
        elif cmd == "R":
            lines.append(f"R {args[0]:02X}       # {note}")
        else:
            lines.append(f"F          # {note}")
    return lines


def strip(lines: List[str]) -> List[str]:
    out = []
    for ln in lines:
        s = ln.split("#", 1)[0].strip()
        if s:
            out.append(s)
    return out


def count_xfers(lines: List[str]) -> int:
    return sum(1 for s in strip(lines) if s.split()[0] in ("W", "R"))
