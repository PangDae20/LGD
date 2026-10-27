"""[4단계-보조] RTL 시뮬레이션 결과 기록/재생.

iverilog가 있는 PC에서 실행한 결과를 <IP>/.sim_cache/<키>/ 에 저장해 두고,
iverilog가 없는 PC에서 '같은 RTL + 같은 벡터 + 같은 인터페이스'로 실행하면 그 기록을 재생한다.
키 = RTL 파일 내용 + 테스트벤치 내용 + top + 인터페이스 + I2C 주소 + 명령 벡터 의 SHA-256
(경로·줄바꿈 형식과 무관하게 내용이 같으면 같은 키)
기록이 없으면 Python 모델로 대체한다.
"""
import glob
import hashlib
import os
import shutil
from typing import Callable, List

from .datatypes import RawResult
from .model_runner import ModelBackend
from .vector_cmd import count_xfers, strip

TB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tb")
CACHE_DIR = ".sim_cache"


def _norm(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def cache_key(rtl_files: List[str], top: str, iface: str, i2c_addr: int, lines: List[str]) -> str:
    h = hashlib.sha256()
    for p in sorted(rtl_files, key=os.path.basename):
        h.update(os.path.basename(p).encode() + b"\0" + _norm(p) + b"\0")
    for p in sorted(glob.glob(os.path.join(TB_DIR, "*"))):
        h.update(os.path.basename(p).encode() + b"\0" + _norm(p) + b"\0")
    h.update(f"{top}|{iface}|{i2c_addr:02X}|".encode())
    h.update("\n".join(strip(lines)).encode())
    return h.hexdigest()[:20]


def save(ip: str, key: str, workdir: str):
    dst = os.path.join(ip, CACHE_DIR, key)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for fn in os.listdir(workdir):
        if fn == "sim_log.txt" or fn.startswith("frame_"):
            shutil.copy2(os.path.join(workdir, fn), os.path.join(dst, fn))


class ReplayBackend:
    """iverilog 없을 때: 기록된 RTL 결과 재생, 기록 없으면 Python 모델"""

    def __init__(self, rm, ip: str, rtl_files: List[str], top: str, iface: str, i2c_addr: int):
        self.rm, self.ip = rm, ip
        self.rtl_files, self.top, self.iface, self.i2c_addr = rtl_files, top, iface, i2c_addr
        self.name = f"RTL 시뮬레이션 기록 재생 ({iface.upper()}, iverilog 없음)"
        self.replayed = 0
        self.fallback = 0

    def run(self, lines: List[str], log: Callable[[str], None] = print) -> RawResult:
        from .sim_runner import parse_log
        key = cache_key(self.rtl_files, self.top, self.iface, self.i2c_addr, lines)
        d = os.path.join(self.ip, CACHE_DIR, key)
        if os.path.exists(os.path.join(d, "sim_log.txt")):
            self.replayed += 1
            log(f"[기록 재생] iverilog 없음 -> 같은 RTL·벡터로 실행했던 RTL 시뮬레이션 결과 사용 (키 {key}, "
                f"{self.iface.upper()} 트랜잭션 {count_xfers(lines)}개)")
            return parse_log(os.path.join(d, "sim_log.txt"), os.path.join(d, "frame"), log)
        self.fallback += 1
        log(f"[대체] 이 조합의 RTL 기록 없음 (키 {key}) -> Python 모델로 실행 (프로토콜 파형 없음)")
        little = self.rm.ip.get("rtl_byte_order_hint", self.rm.spec_byte_order) == "little"
        return ModelBackend(self.rm, little).run(lines, log)
