"""[4단계] 선택한 RTL + 공통 하네스(tool/tb)를 iverilog로 컴파일해 SPI/I2C로 인가.

작업 파일 (workdir, 디버깅 시 직접 열어볼 수 있음)
  cmd_vectors.txt  하네스 입력 명령
  sim_log.txt      읽기 결과 원본 ("R aa dd [NACK]", "F n pixels|TIMEOUT")
  frame_<n>.hex    캡처한 프레임 (픽셀당 RRGGBB 한 줄)
  compile.log      iverilog 출력
"""
import os
import shutil
import subprocess
from typing import Callable, List, Optional, Tuple

from .datatypes import RawResult
from .vector_cmd import count_xfers, strip

TB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tb")
HARNESS = os.path.join(TB_DIR, "tb_harness.v")


BUNDLED_BIN = os.path.join(os.path.dirname(TB_DIR), "third_party", "iverilog", "bin")

# 찾는 순서: 1) 툴에 동봉한 포터블판  2) PATH  3) Windows 기본 설치 경로
SEARCH = [("동봉판 (tool/third_party/iverilog)", BUNDLED_BIN), ("시스템 PATH", None),
          ("기본 설치 경로", r"C:\iverilog\bin"), ("기본 설치 경로", r"C:\Program Files\iverilog\bin")]


def locate_iverilog() -> Optional[Tuple[str, str, str]]:
    """(iverilog 경로, vvp 경로, 출처) 또는 None"""
    for label, d in SEARCH:
        if d is not None and not os.path.isdir(d):
            continue
        iv = shutil.which("iverilog", path=d) if d else shutil.which("iverilog")
        vv = shutil.which("vvp", path=d) if d else shutil.which("vvp")
        if iv and vv:
            return iv, vv, label
    return None


def find_iverilog() -> Optional[Tuple[str, str]]:
    t = locate_iverilog()
    return (t[0], t[1]) if t else None


class SimBackend:
    def __init__(self, rtl_files: List[str], top: str, iface: str, i2c_addr: int, workdir: str):
        tools = find_iverilog()
        if not tools:
            raise RuntimeError("iverilog/vvp 를 찾을 수 없음 -> 'Python 모델' 백엔드를 사용하세요")
        self.iverilog, self.vvp = tools
        self.rtl_files, self.top = rtl_files, top
        self.iface, self.i2c_addr = iface, i2c_addr
        self.workdir = os.path.abspath(workdir)
        os.makedirs(self.workdir, exist_ok=True)
        self.binary = os.path.join(self.workdir, "sim.vvp")
        self.name = f"RTL 시뮬레이션 (iverilog, {iface.upper()})"
        self._compiled = False

    def compile(self, log: Callable[[str], None] = print):
        cmd = [self.iverilog, "-g2005", f"-I{TB_DIR}", f"-DDUT_TOP={self.top}", "-o", self.binary, HARNESS] + self.rtl_files
        log(f"RTL 컴파일: top={self.top}, 파일 {len(self.rtl_files)}개")
        p = subprocess.run(cmd, capture_output=True, text=True)
        with open(os.path.join(self.workdir, "compile.log"), "w") as f:
            f.write(" ".join(cmd) + "\n\n" + p.stdout + p.stderr)
        if p.returncode != 0:
            raise RuntimeError("RTL 컴파일 실패\n" + p.stderr)
        self._compiled = True

    def run(self, lines: List[str], log: Callable[[str], None] = print) -> RawResult:
        if not self._compiled:
            self.compile(log)
        vec = os.path.join(self.workdir, "cmd_vectors.txt")
        slog = os.path.join(self.workdir, "sim_log.txt")
        fpre = os.path.join(self.workdir, "frame")
        with open(vec, "w") as f:
            f.write("\n".join(strip(lines)) + "\n")
        for fn in os.listdir(self.workdir):
            if fn.startswith("frame_"):
                os.remove(os.path.join(self.workdir, fn))
        log(f"시뮬레이션: {self.iface.upper()} 트랜잭션 {count_xfers(lines)}개 인가")
        # vvp 에는 상대 경로만 넘긴다 (cwd=workdir). Windows 에서 한글 등 비ASCII 경로를 vvp 가 못 여는 문제 회피
        args = [self.vvp, "-n", "sim.vvp", "+VEC=cmd_vectors.txt", "+LOG=sim_log.txt", "+FRAME=frame",
                f"+IF={1 if self.iface == 'i2c' else 0}", f"+DEV={self.i2c_addr:02X}"]
        p = subprocess.run(args, capture_output=True, text=True, cwd=self.workdir)
        if p.returncode != 0:
            raise RuntimeError("시뮬레이션 실패\n" + p.stdout + p.stderr)
        return parse_log(slog, fpre, log)


def parse_log(slog: str, fpre: str, log: Callable[[str], None] = print) -> RawResult:
    res = RawResult()
    with open(slog) as f:
        for ln in f:
            tok = ln.split()
            if not tok:
                continue
            if tok[0] == "R":
                res.reads.append((int(tok[1], 16), int(tok[2], 16), "NACK" in tok))
            elif tok[0] == "W" and "NACK" in tok:
                log(f"[경고] 쓰기 NACK: addr 0x{tok[1]}")
            elif tok[0] == "F":
                if tok[2] == "TIMEOUT":
                    res.frames.append(None)
                else:
                    px = []
                    with open(f"{fpre}_{tok[1]}.hex") as ff:
                        for h in ff:
                            h = h.strip()
                            if h:
                                px.append((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
                    res.frames.append(px)
    return res
