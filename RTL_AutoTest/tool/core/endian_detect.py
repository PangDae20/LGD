"""[5단계] ID 레지스터로 실제 바이트 순서(엔디안) 판단.

사양서 순서로 ID 레지스터를 읽어서
  - 리셋값과 같으면           -> 사양서 순서가 맞음
  - 바이트가 뒤집힌 값이면    -> 실제 칩은 반대 순서
  - NACK                      -> 인터페이스/장치 주소 문제
  - 그 외                     -> 엔디안 문제가 아님 (연결·칩 확인)
"""
from typing import Tuple

from .datatypes import Op, TestCase
from .judge import judge
from .regmap import RegMap
from .vector_cmd import serialize


def detect_byte_order(backend, rm: RegMap, log=print) -> Tuple[str, str]:
    spec = rm.spec_byte_order
    r = rm[rm.id_register]
    probe = TestCase("ID", "id_check", "probe", [Op("RST"), Op("RREG", r.name, r.reset, r.full_mask)])
    raw = backend.run(serialize([probe], rm, spec), log)
    res = judge([probe], rm, spec, raw)[0]
    if res.passed:
        return spec, f"{r.name}={res.actual} 일치 -> 사양서 바이트 순서({spec}) 사용"
    if "NACK" in res.note:
        return spec, f"{r.name} 읽기 실패: {res.note}"
    other = "little" if spec == "big" else "big"
    if "엔디안" in res.note:
        return other, (f"{r.name} 기대 {res.expected}, 실측 {res.actual} -> 바이트가 뒤집혀 읽힘. "
                       f"사양서({spec})와 실제 칩이 다름 -> {other}-endian 으로 전환")
    return spec, f"{r.name} 기대 {res.expected}, 실측 {res.actual} -> 엔디안 문제 아님 (연결/칩 확인 필요)"
