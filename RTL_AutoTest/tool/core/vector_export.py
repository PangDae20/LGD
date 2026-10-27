"""[3단계] 테스트벡터 RTL -> Aardvark 배치(XML) 파일 (툴의 주 출력).

인터페이스(SPI / I2C)에 따라 Aardvark Control Center 배치 명령으로 변환한다.
각 동작 줄 끝 주석에 원래 테스트벡터 RTL 줄 번호(L<n>)와 읽기 기대값을 남겨,
변환 결과를 RTL로 거슬러 확인할 수 있다. (GUI는 줄별 RTL 위치 목록 srcs 로 양방향 강조)
"""
from typing import List, Optional, Tuple

from . import vector_aardvark as av
from .datatypes import TestCase
from .regmap import RegMap
from .vector_cmd import expand

IND = "  "


def export_with_map(cases: List[TestCase], rm: RegMap, order: str, iface: str, i2c_addr: int,
                    header: bool = True) -> Tuple[List[str], List[Optional[str]]]:
    """반환: (출력 줄, 각 줄의 RTL 위치 '파일:줄' 또는 None)"""
    out: List[str] = []
    srcs: List[Optional[str]] = []

    def add(line, src=None):
        out.append(line)
        srcs.append(src)

    if header:
        for h in av.header(iface, i2c_addr, rm.name, order):
            add(h)
    idx = 0
    for cmd, args, note, src in expand(cases, rm, order):
        if cmd == "#":
            add(IND + av.comment("## " + note))
            continue
        ln = "L" + src.rsplit(":", 1)[-1] if src else ""
        if cmd == "RST":
            body, tag = av.reset(), "reset"
        elif cmd == "F":
            body, tag = av.capture(note), "capture"
        elif cmd == "W":
            a, d = args
            body = [av.spi_write(a, d)] if iface == "spi" else av.i2c_write(i2c_addr, a, d)
            tag = note
        else:
            a, exp, msk = args
            body = [av.spi_read(a)] if iface == "spi" else av.i2c_read(i2c_addr, a)
            tag = "{}  expect 0x{:02X} mask 0x{:02X}".format(note, exp, msk)
        for i, b in enumerate(body):
            last = (i == len(body) - 1)
            cm = av.comment("{:05d} {} {}".format(idx, ln, tag)) if last and not b.startswith("<!--") else ""
            if b.startswith("<!--") and last is False:
                add(IND + b, src)
            elif b.startswith("<!--"):
                add(IND + b[:-4].rstrip() + "  {:05d} {} -->".format(idx, ln), src)
            else:
                add(IND + b.ljust(64) + cm, src)
        idx += 1
    if header:
        for f in av.footer():
            add(f)
    return out, srcs


def export(cases: List[TestCase], rm: RegMap, order: str, iface: str, i2c_addr: int) -> List[str]:
    return export_with_map(cases, rm, order, iface, i2c_addr)[0]
