"""[5단계] 판정: 인가 결과(RawResult)와 기대값 비교.

기대값 우선순위: 사람이 지정한 값(02_regmap/expected_overrides.yaml) > 자동 계산값
"""
import os
from typing import Dict, List, Optional

from .datatypes import RawResult, Result, TestCase
from .golden_model import tpg_frame
from .regmap import RegMap, swap_bytes


def load_image_pixels(path: str):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    return im.width, im.height, list(im.getdata())


def judge_register(res: Result, expected: int):
    res.expected = f"0x{expected:0{max(res.width // 4, 2)}X}"
    res.passed = res.actual_val is not None and (res.actual_val & res.mask) == (expected & res.mask)


def judge_frame(res: Result, gw: int, gh: int, gold: list):
    cap = res.frame["captured"]
    res.frame.update({"w": gw, "h": gh, "golden": gold})
    res.expected = f"{gw}x{gh} = {len(gold)} px"
    if cap is None:
        res.passed, res.actual, res.note = False, "출력 없음", "프레임 시작 신호 없음 (표시 꺼짐?)"
        return
    res.actual = f"{len(cap)} px"
    if len(cap) != len(gold):
        res.passed, res.note = False, f"픽셀 수 다름 (기대 {len(gold)}, 실제 {len(cap)})"
    else:
        diff = sum(1 for a, b in zip(gold, cap) if a != b)
        res.passed, res.note = diff == 0, ("" if diff == 0 else f"불일치 픽셀 {diff}개")


def judge(cases: List[TestCase], rm: RegMap, order: str, raw: RawResult,
          overrides: Optional[Dict[str, dict]] = None, ip_dir: str = ".") -> List[Result]:
    overrides = overrides or {}
    out: List[Result] = []
    ri = fi = 0
    for tc in cases:
        for op in tc.ops:
            if op.kind == "RREG":
                r = rm[op.reg]
                bytes_read, nack = {}, False
                for a, _ in rm.byte_lanes(r, order):
                    ra, rd, nk = raw.reads[ri]
                    ri += 1
                    if ra != a:
                        raise RuntimeError(f"벡터/결과 순서 불일치: 기대 주소 0x{a:02X}, 결과 0x{ra:02X}")
                    bytes_read[a] = rd
                    nack |= nk
                act = rm.join(r, bytes_read, order)
                item = f"{r.name} {op.label}".strip()
                res = Result(tc.tid, tc.ttype, item, "", f"0x{act:0{r.nbytes * 2}X}", False,
                             key=f"{tc.tid}|{item}", width=r.width, actual_val=act, mask=op.mask)
                exp = op.value
                ov = overrides.get(res.key)
                if ov and "value" in ov:
                    exp, res.exp_src = int(str(ov["value"]), 0), "지정"
                judge_register(res, exp)
                if nack:
                    res.passed, res.note, res.actual_val = False, "I2C NACK (장치 주소 확인)", None
                elif not res.passed and r.nbytes > 1 and act == swap_bytes(exp, r.nbytes):
                    res.note = "바이트 순서 반대로 읽힘 -> 엔디안 불일치 의심"
                out.append(res)
            elif op.kind == "FRAME":
                cap = raw.frames[fi]
                fi += 1
                res = Result(tc.tid, tc.ttype, op.label, "", "", False, key=f"{tc.tid}|{op.label}",
                             frame={"captured": cap})
                ov = overrides.get(res.key)
                if ov and "image" in ov and os.path.exists(os.path.join(ip_dir, ov["image"])):
                    gw, gh, gold = load_image_pixels(os.path.join(ip_dir, ov["image"]))
                    res.exp_src = "지정: " + ov["image"]
                else:
                    gw, gh, gold = tpg_frame(op.golden)
                judge_frame(res, gw, gh, gold)
                out.append(res)
    if ri != len(raw.reads) or fi != len(raw.frames):
        raise RuntimeError(f"결과 수 불일치: 읽기 {ri}/{len(raw.reads)}, 프레임 {fi}/{len(raw.frames)}")
    return out
