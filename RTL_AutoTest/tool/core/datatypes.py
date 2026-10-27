"""단계 사이에 주고받는 자료형 (디버깅 시 각 단계의 입력/출력 형태를 여기서 확인)."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Op:
    """레지스터 단위 동작 (tv_parser 출력, 엔디안/인터페이스와 무관)"""
    kind: str                    # RST / WREG / RREG / FRAME
    reg: Optional[str] = None
    value: int = 0               # WREG: 쓸 값 / RREG: 기대값
    mask: int = 0                # RREG: 비교 마스크
    label: str = ""
    golden: Optional[Dict[str, int]] = None   # FRAME: 기대 레지스터 상태
    src: str = ""                # 테스트벡터 RTL 위치 "01_input/testvector/tv_t03.v:12"
    text: str = ""               # 원래 RTL 문장


@dataclass
class TestCase:
    """테스트벡터 RTL 파일 1개 = 시험 1개"""
    tid: str
    ttype: str
    desc: str
    ops: List[Op] = field(default_factory=list)
    src_file: str = ""


@dataclass
class RawResult:
    """인가 결과 원본 (sim_runner / model_runner 출력)"""
    reads: List[Tuple[int, int, bool]] = field(default_factory=list)   # (byte addr, data, nack)
    frames: List[Optional[list]] = field(default_factory=list)         # None = 프레임 없음


@dataclass
class Result:
    """판정 결과 1행 (judge 출력)"""
    tid: str
    ttype: str
    item: str
    expected: str
    actual: str
    passed: bool
    note: str = ""
    frame: Optional[dict] = None     # 화면 시험: {w, h, golden, captured}
    key: str = ""                    # 기대값 지정 키 "T03|H_ACTIVE pat=0x5555"
    width: int = 0
    actual_val: Optional[int] = None
    mask: int = 0
    exp_src: str = "자동"            # 자동 / 지정
