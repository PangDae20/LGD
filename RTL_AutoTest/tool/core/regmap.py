"""[1단계] IP별 레지스터맵 (02_regmap/regmap.yaml) 로딩·저장·검증 + 바이트 주소 매핑.

엔디안 처리는 이 파일의 byte_lanes() 한 곳에만 있다.
"""
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

import yaml

FIELDS = ["name", "addr", "width", "access", "reset", "rw_mask", "desc", "volatile"]


@dataclass
class Register:
    name: str
    addr: int
    width: int
    access: str
    reset: int
    rw_mask: int
    desc: str = ""
    volatile: bool = False

    @property
    def nbytes(self) -> int:
        return self.width // 8

    @property
    def full_mask(self) -> int:
        return (1 << self.width) - 1


def _int(v):
    if isinstance(v, int):
        return v
    s = str(v).strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


class RegMap:
    def __init__(self, ip: dict, regs: List[Register], path: str = ""):
        self.ip = ip
        self.regs = regs
        self.path = path

    # ---------------------------------------------------------------- io
    @classmethod
    def load(cls, path: str) -> "RegMap":
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        regs = []
        for r in raw.get("registers", []):
            regs.append(Register(name=str(r["name"]), addr=_int(r["addr"]), width=_int(r["width"]),
                                 access=str(r["access"]).upper(), reset=_int(r["reset"]),
                                 rw_mask=_int(r["rw_mask"]), desc=str(r.get("desc", "")),
                                 volatile=bool(r.get("volatile", False))))
        rm = cls(raw.get("ip", {}), regs, path)
        rm.validate()
        return rm

    def save(self, path: str = None):
        path = path or self.path
        ip = dict(self.ip)
        if "i2c_addr" in ip:
            ip["i2c_addr"] = f"0x{_int(ip['i2c_addr']):02X}"
        lines = ["# IP 레지스터맵: 레지스터 정의 헤더(.vh)에서 추출한 초안을 사양서와 대조해 확정한 것 (IP마다 별도 파일)",
                 yaml.safe_dump({"ip": ip}, allow_unicode=True, sort_keys=False).rstrip(), "registers:"]
        for r in self.regs:
            w = r.nbytes * 2
            vol = ", volatile: true" if r.volatile else ""
            lines.append(f"  - {{name: {r.name}, addr: 0x{r.addr:02X}, width: {r.width}, access: {r.access}, "
                         f"reset: 0x{r.reset:0{w}X}, rw_mask: 0x{r.rw_mask:0{w}X}, desc: \"{r.desc}\"{vol}}}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.path = path

    def validate(self):
        names = set()
        used = {}
        for r in self.regs:
            if r.name in names:
                raise ValueError(f"레지스터 이름 중복: {r.name}")
            names.add(r.name)
            if r.width not in (8, 16, 24, 32):
                raise ValueError(f"{r.name}: width는 8/16/24/32 중 하나")
            if r.access not in ("RO", "RW"):
                raise ValueError(f"{r.name}: access는 RO 또는 RW")
            for a in range(r.addr, r.addr + r.nbytes):
                if a in used:
                    raise ValueError(f"주소 겹침: 0x{a:02X} ({used[a]}, {r.name})")
                used[a] = r.name
        if self.id_register and self.id_register not in names:
            raise ValueError(f"id_register '{self.id_register}' 가 레지스터 목록에 없음")

    # ---------------------------------------------------------- properties
    @property
    def name(self):
        return self.ip.get("name", "IP")

    @property
    def spec_byte_order(self):
        return self.ip.get("byte_order", "big")

    @property
    def id_register(self):
        return self.ip.get("id_register")

    @property
    def i2c_addr(self):
        return _int(self.ip.get("i2c_addr", 0x3C))

    def __getitem__(self, name: str) -> Register:
        for r in self.regs:
            if r.name == name:
                return r
        raise KeyError(name)

    # ---------------------------------------------------------- byte lanes
    @staticmethod
    def byte_lanes(reg: Register, order: str) -> List[Tuple[int, int]]:
        """레지스터 -> [(byte_addr, bit_shift), ...]
        big    : 낮은 주소 = 상위 바이트 / little : 낮은 주소 = 하위 바이트"""
        n = reg.nbytes
        if order not in ("big", "little"):
            raise ValueError(f"unknown byte order: {order}")
        return [(reg.addr + i, 8 * (n - 1 - i) if order == "big" else 8 * i) for i in range(n)]

    def split(self, reg: Register, value: int, order: str) -> List[Tuple[int, int]]:
        return [(a, (value >> s) & 0xFF) for a, s in self.byte_lanes(reg, order)]

    def join(self, reg: Register, byte_vals: Dict[int, int], order: str) -> int:
        v = 0
        for a, s in self.byte_lanes(reg, order):
            v |= (byte_vals[a] & 0xFF) << s
        return v


def swap_bytes(value: int, nbytes: int) -> int:
    out = 0
    for i in range(nbytes):
        out = (out << 8) | ((value >> (8 * i)) & 0xFF)
    return out


if __name__ == "__main__":
    # 디버그: python -m core.regmap <regmap.yaml>  -> 검증 + 레지스터별 바이트 주소 표
    import sys
    rm = RegMap.load(sys.argv[1])
    print(f"{rm.name}: {len(rm.regs)} regs, byte_order={rm.spec_byte_order}, id={rm.id_register}")
    for r in rm.regs:
        big = [f"0x{a:02X}<<{s}" for a, s in rm.byte_lanes(r, "big")]
        lit = [f"0x{a:02X}<<{s}" for a, s in rm.byte_lanes(r, "little")]
        print(f"  {r.name:11s} {r.access} w={r.width:2d} reset=0x{r.reset:X} mask=0x{r.rw_mask:X}  big={big} little={lit}")
