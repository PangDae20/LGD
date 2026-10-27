"""[1단계] RTL -> 레지스터맵 초안 추출.

규칙
- 레지스터 주소:  localparam [..] ADDR_<NAME> = <N>'h<hex>;
- 속성(선택):     같은 줄 주석  // REG width=16 access=RW reset=0x0040 rw_mask=0x07FF desc="..."
  속성 주석이 없으면 주소만 채우고 나머지는 '확인 필요'로 남긴다 -> 사람이 표에서 수정.
- 힌트:           top 모듈 이름, I2C 장치 주소 파라미터(I2C_ADDR), 바이트 순서 파라미터(ADDR_LE)
"""
import os
import re
import shlex
from typing import Dict, List, Tuple

RE_ADDR = re.compile(r"localparam\s*(?:\[[^\]]*\])?\s*ADDR_(\w+)\s*=\s*([^;]+?)\s*;(.*)$")
RE_VNUM = re.compile(r"^(\d+)?\s*'\s*[sS]?([hHdDbBoO])\s*([0-9a-fA-F_]+)$")


def parse_vnum(s: str) -> int:
    """Verilog 숫자 -> int. 7'h0A / 7'd10 / 7'b0001010 / 10 (진법 없으면 10진수) / 0x0A"""
    s = s.strip()
    m = RE_VNUM.match(s)
    if m:
        base = {"h": 16, "d": 10, "b": 2, "o": 8}[m.group(2).lower()]
        return int(m.group(3).replace("_", ""), base)
    return int(s.replace("_", ""), 0)
RE_MODULE = re.compile(r"^\s*module\s+(\w+)", re.M)
RE_INST = re.compile(r"^\s*(\w+)\s*(?:#\s*\(.*?\))?\s+\w+\s*\(", re.M | re.S)
RE_I2C = re.compile(r"(?:parameter|localparam)\s*(?:\[[^\]]*\])?\s*I2C_(?:DEV_)?ADDR\s*=\s*\d*'h([0-9a-fA-F]+)")
RE_LE = re.compile(r"parameter\s+ADDR_LE\s*=\s*(\d)")

KEYWORDS = {"module", "if", "else", "case", "begin", "end", "assign", "always", "for", "while", "wire", "reg"}


def _parse_attrs(comment: str) -> Dict[str, str]:
    c = comment.strip()
    if not c.startswith("//"):
        return {}
    c = c[2:].strip()
    if not c.startswith("REG"):
        return {}
    out = {}
    for tok in shlex.split(c[3:]):
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def extract(files: List[str], base_dir: str = None) -> Tuple[dict, List[dict], List[str]]:
    """반환: (ip 힌트, 레지스터 dict 리스트, 경고 메시지)"""
    regs: List[dict] = []
    warns: List[str] = []
    modules, instantiated = [], set()
    hints: dict = {}
    texts = {}
    for path in files:
        with open(path, encoding="utf-8", errors="replace") as f:
            texts[path] = f.read()

    for path, txt in texts.items():
        fn = os.path.relpath(path, base_dir).replace("\\", "/") if base_dir else os.path.basename(path)
        modules += RE_MODULE.findall(txt)
        for m in RE_INST.findall(txt):
            if m not in KEYWORDS:
                instantiated.add(m)
        for ln_no, ln in enumerate(txt.splitlines(), 1):
            m = RE_ADDR.search(ln)
            if not m:
                continue
            name, comment = m.group(1), m.group(3)
            try:
                addr = parse_vnum(m.group(2))
            except ValueError:
                warns.append(f"{name} ({fn}:{ln_no}) 주소 '{m.group(2)}' 해석 불가 -> 제외")
                continue
            a = _parse_attrs(comment)
            r = {"name": name, "addr": addr,
                 "width": int(a.get("width", 8)),
                 "access": a.get("access", "RW").upper(),
                 "reset": int(a.get("reset", "0"), 0),
                 "rw_mask": int(a.get("rw_mask", "0"), 0) if "rw_mask" in a else None,
                 "desc": a.get("desc", ""),
                 "volatile": a.get("volatile", "0") in ("1", "true", "yes"),
                 "src": f"{fn}:{ln_no}"}
            missing = [k for k in ("width", "access", "reset", "rw_mask") if k not in a]
            if missing:
                r["desc"] = (r["desc"] + " [확인 필요: " + ",".join(missing) + "]").strip()
                warns.append(f"{name} ({fn}:{ln_no}) 속성 없음 -> {', '.join(missing)} 확인 필요")
            if r["rw_mask"] is None:
                r["rw_mask"] = ((1 << r["width"]) - 1) if r["access"] == "RW" else 0
            regs.append(r)
        m = RE_I2C.search(txt)
        if m and "i2c_addr" not in hints:
            hints["i2c_addr"] = int(m.group(1), 16)
        m = RE_LE.search(txt)
        if m and "rtl_byte_order" not in hints:
            hints["rtl_byte_order"] = "little" if m.group(1) == "1" else "big"

    tops = [m for m in modules if m not in instantiated]
    if tops:
        hints["top"] = tops[0]
        if len(tops) > 1:
            warns.append(f"top 후보가 여러 개: {', '.join(tops)} -> {tops[0]} 사용")
    if not regs:
        warns.append("ADDR_<NAME> 형태의 레지스터 주소 정의를 찾지 못함")
    regs.sort(key=lambda r: r["addr"])
    return hints, regs, warns


if __name__ == "__main__":
    # 디버그: python -m core.rtl_parser <rtl 파일들...>  -> 추출 표, 힌트, 경고
    import sys
    h, regs, warns = extract(sys.argv[1:])
    print("hints:", h)
    for r in regs:
        print(f"  0x{r['addr']:02X} {r['name']:11s} w={r['width']:2d} {r['access']} reset=0x{r['reset']:X} "
              f"mask=0x{r['rw_mask']:X}  <- {r['src']}")
    for w in warns:
        print("  [확인]", w)
