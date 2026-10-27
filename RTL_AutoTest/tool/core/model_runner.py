"""[4단계-대체] 시뮬레이터가 없을 때 쓰는 Python 동작 모델.

RTL과 같은 레지스터 동작(RO 무시, 예약 비트 0, 바이트 순서)을 흉내낸다. 프로토콜 계층(SPI/I2C 파형)은 생략.
RTL 시뮬레이션 결과와 이 모델 결과가 같은지 비교하면 판정 로직과 RTL을 서로 교차 검증할 수 있다.
"""
from typing import Callable, List

from .datatypes import RawResult
from .golden_model import Pixel, tpg_frame
from .regmap import RegMap
from .vector_cmd import strip


class ChipModel:
    def __init__(self, rm: RegMap, little: bool):
        self.rm = rm
        self.order = "little" if little else "big"
        self.reset()

    def reset(self):
        self.val = {r.name: r.reset for r in self.rm.regs}

    def _lookup(self, addr: int):
        for r in self.rm.regs:
            for a, s in self.rm.byte_lanes(r, self.order):
                if a == addr:
                    return r, s
        return None, 0

    def display_on(self) -> bool:
        return "DISP_CTRL" in self.val and (self.val["DISP_CTRL"] & 3) == 3

    def write(self, addr: int, data: int):
        r, s = self._lookup(addr)
        if r is None or r.access != "RW":
            return
        lane = (0xFF << s) & r.rw_mask
        self.val[r.name] = (self.val[r.name] & ~lane) | ((data << s) & lane)

    def read(self, addr: int) -> int:
        r, s = self._lookup(addr)
        if r is None:
            return 0
        v = int(self.display_on()) if r.name == "STATUS" else self.val[r.name]
        return (v >> s) & 0xFF

    def frame(self) -> List[Pixel]:
        return tpg_frame(self.val)[2]


class ModelBackend:
    name = "Python 모델"

    def __init__(self, rm: RegMap, little: bool):
        self.rm, self.little = rm, little

    def run(self, lines: List[str], log: Callable[[str], None] = print) -> RawResult:
        chip = ChipModel(self.rm, self.little)
        res = RawResult()
        for s in strip(lines):
            tok = s.split()
            if tok[0] == "RST":
                chip.reset()
            elif tok[0] == "W":
                chip.write(int(tok[1], 16), int(tok[2], 16))
            elif tok[0] == "R":
                a = int(tok[1], 16)
                res.reads.append((a, chip.read(a), False))
            elif tok[0] == "F":
                res.frames.append(chip.frame() if chip.display_on() else None)
        return res
