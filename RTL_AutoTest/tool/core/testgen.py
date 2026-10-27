"""[2단계] 템플릿 + 레지스터맵 -> 레지스터 단위 시험 동작(TestCase / Op).

엔디안·인터페이스와 무관한 '레지스터 단위' 동작만 만든다.
바이트 단위로 펼치는 건 vector_cmd / vector_spi / vector_i2c 에서 처리.
"""
from typing import Dict, List

import yaml

from .datatypes import Op, TestCase
from .regmap import RegMap


def _state_after(rm: RegMap, writes: Dict[str, int]) -> Dict[str, int]:
    st = {r.name: r.reset for r in rm.regs}
    for n, v in writes.items():
        r = rm[n]
        if r.access == "RW":
            st[n] = (st[n] & ~r.rw_mask) | (v & r.rw_mask)
    return st


def generate(rm: RegMap, template_path: str) -> List[TestCase]:
    with open(template_path, encoding="utf-8") as f:
        tpl = yaml.safe_load(f)

    cases: List[TestCase] = []
    for t in tpl["tests"]:
        tc = TestCase(t["id"], t["type"], t.get("desc", t["type"]))
        ops = tc.ops
        typ = t["type"]

        if typ == "id_check":
            r = rm[rm.id_register]
            ops += [Op("RST"), Op("RREG", r.name, r.reset, r.full_mask, "ID")]

        elif typ == "reset_check":
            ops.append(Op("RST"))
            for r in rm.regs:
                ops.append(Op("RREG", r.name, r.reset, r.full_mask, "reset"))

        elif typ == "rw_pattern":
            for pat in t["patterns"]:
                ops.append(Op("RST"))
                for r in rm.regs:
                    if r.access != "RW":
                        continue
                    p = pat & r.full_mask
                    ops.append(Op("WREG", r.name, p))
                    ops.append(Op("RREG", r.name, p & r.rw_mask, r.full_mask, f"pat=0x{p:0{r.nbytes*2}X}"))

        elif typ == "walking_one":
            for r in rm.regs:
                if r.access != "RW":
                    continue
                ops.append(Op("RST"))
                for bit in range(r.width):
                    if not (r.rw_mask >> bit) & 1:
                        continue
                    p = 1 << bit
                    ops.append(Op("WREG", r.name, p))
                    ops.append(Op("RREG", r.name, p, r.full_mask, f"bit{bit}"))

        elif typ == "ro_protect":
            ops.append(Op("RST"))
            for r in rm.regs:
                if r.access != "RO" or r.volatile:
                    continue
                inv = (~r.reset) & r.full_mask
                ops.append(Op("WREG", r.name, inv))
                ops.append(Op("RREG", r.name, r.reset, r.full_mask, "write ~reset"))

        elif typ == "reserved_bits":
            ops.append(Op("RST"))
            for r in rm.regs:
                if r.access != "RW" or r.rw_mask == r.full_mask:
                    continue
                ops.append(Op("WREG", r.name, r.full_mask))
                ops.append(Op("RREG", r.name, r.rw_mask, r.full_mask, "write all-1"))

        elif typ == "functional":
            need = {"H_ACTIVE", "V_ACTIVE", "TPG_MODE", "FG_R", "FG_G", "FG_B", "CHECKER_SZ", "PIX_CTRL", "DISP_CTRL"}
            have = {r.name for r in rm.regs}
            if not need <= have:
                continue          # 화면 출력 레지스터가 없는 IP는 기능 시험 생략
            for sc in t["scenarios"]:
                regs = dict(sc["regs"])
                ops.append(Op("RST"))
                # 표시 켜기(DISP_CTRL)는 다른 설정을 끝낸 뒤 마지막에
                order = [k for k in regs if k != "DISP_CTRL"] + (["DISP_CTRL"] if "DISP_CTRL" in regs else [])
                for k in order:
                    ops.append(Op("WREG", k, regs[k]))
                ops.append(Op("FRAME", label=sc["name"], golden=_state_after(rm, regs)))
        else:
            raise ValueError(f"unknown test type: {typ}")

        cases.append(tc)
    return cases


def summarize(cases: List[TestCase]) -> List[str]:
    out = []
    for tc in cases:
        k = {}
        for op in tc.ops:
            k[op.kind] = k.get(op.kind, 0) + 1
        out.append(f"{tc.tid} {tc.ttype:13s} {tc.desc:20s} " + " ".join(f"{a}={b}" for a, b in k.items()))
    return out


if __name__ == "__main__":
    # 디버그: python -m core.testgen <regmap.yaml> <template.yaml> [시험ID]  -> 시험별 동작 수, 지정 시험의 동작 목록
    import sys
    rm = RegMap.load(sys.argv[1])
    cases = generate(rm, sys.argv[2])
    print("\n".join(summarize(cases)))
    if len(sys.argv) > 3:
        for tc in cases:
            if tc.tid == sys.argv[3]:
                for op in tc.ops:
                    print(f"  {op.kind:5s} {op.reg or '':11s} value=0x{op.value:X} mask=0x{op.mask:X} {op.label}")
