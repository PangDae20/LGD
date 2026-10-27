"""IP 작업공간(디렉토리) 구조.

<프로젝트>/<IP 이름>/
  01_input/testvector/     입력: 테스트벡터 RTL (tv_*.v) + 레지스터 정의 헤더 (*_regmap.vh)
  01_input/spec/           사양서
  02_regmap/regmap.yaml    IP별 레지스터맵 (헤더에서 추출 -> 검토 -> 저장)
  03_vectors/spi|i2c/      출력: SPI / I2C 포맷으로 변환한 테스트벡터 (파일별 + all)
  ---- For Demo (실물 칩 + 장비 대신 RTL 시뮬레이션) ----
  demo_dut/rtl/            실물 칩 대신 쓰는 DUT RTL
  02_regmap/expected_overrides.yaml, expected/*.png   데모 판정에서 사람이 지정한 기대값
  04_results/<실행>/       데모 인가·판정 리포트, debug/(원본 로그)
  .work/                   시뮬레이션 임시 파일
"""
import os
import shutil
from typing import Dict, List

import yaml

TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(TOOL_DIR)
DEFAULT_TEMPLATE = os.path.join(TOOL_DIR, "config", "test_template.yaml")

INPUT_TV = os.path.join("01_input", "testvector")
DEMO_DUT = os.path.join("demo_dut", "rtl")
INPUT_SPEC = os.path.join("01_input", "spec")
REGMAP_DIR = "02_regmap"
VECTORS_DIR = "03_vectors"
RESULTS_DIR = "04_results"
WORK_DIR = ".work"


def p_tv(ip):         return os.path.join(ip, INPUT_TV)
def p_dut(ip):        return os.path.join(ip, DEMO_DUT)
def p_spec(ip):       return os.path.join(ip, INPUT_SPEC)
def p_regmap(ip):     return os.path.join(ip, REGMAP_DIR, "regmap.yaml")
def p_overrides(ip):  return os.path.join(ip, REGMAP_DIR, "expected_overrides.yaml")
def p_expected(ip):   return os.path.join(ip, REGMAP_DIR, "expected")
def p_vectors(ip, iface=None):
    return os.path.join(ip, VECTORS_DIR, iface) if iface else os.path.join(ip, VECTORS_DIR)
def p_results(ip):    return os.path.join(ip, RESULTS_DIR)
def p_work(ip, sub):  return os.path.join(ip, WORK_DIR, sub)


def is_ip_dir(d: str) -> bool:
    return os.path.isdir(p_tv(d))


def list_ips(root: str = PROJECT_ROOT) -> List[str]:
    if not os.path.isdir(root):
        return []
    return sorted(os.path.join(root, d) for d in os.listdir(root)
                  if not d.startswith(".") and is_ip_dir(os.path.join(root, d)))


def _list(ip: str, sub: str, exts) -> List[str]:
    out = []
    for dp, _, fns in os.walk(os.path.join(ip, sub)):
        for fn in fns:
            if fn.endswith(exts):
                out.append(os.path.relpath(os.path.join(dp, fn), ip).replace("\\", "/"))
    return sorted(out)


def list_tv(ip: str) -> List[str]:
    """테스트벡터 RTL (tv_*.v / *.sv). 헤더(.vh)는 제외"""
    return [f for f in _list(ip, INPUT_TV, (".v", ".sv")) if not f.endswith((".vh", ".svh"))]


def list_tv_headers(ip: str) -> List[str]:
    """레지스터 정의 헤더 (*.vh) — 레지스터맵 추출 대상"""
    return _list(ip, INPUT_TV, (".vh", ".svh"))


def list_dut(ip: str) -> List[str]:
    """[For Demo] DUT RTL"""
    return _list(ip, DEMO_DUT, (".v", ".sv", ".vh", ".svh"))


def create_ip(name: str, root: str = PROJECT_ROOT) -> str:
    """IP 이름으로 작업공간 생성"""
    name = name.strip()
    if not name or any(c in name for c in '\\/:*?"<>|'):
        raise ValueError("IP 이름에 사용할 수 없는 문자가 있습니다")
    ip = os.path.join(root, name)
    if os.path.exists(ip):
        raise ValueError(f"이미 있는 IP: {name}")
    for d in (INPUT_TV, INPUT_SPEC, REGMAP_DIR, VECTORS_DIR, RESULTS_DIR, DEMO_DUT):
        os.makedirs(os.path.join(ip, d))
    return ip


def import_files(ip: str, files: List[str], kind: str = "tv") -> List[str]:
    """외부 파일을 01_input/testvector, 01_input/spec, demo_dut/rtl 로 복사"""
    dst = {"tv": p_tv(ip), "spec": p_spec(ip), "dut": p_dut(ip)}[kind]
    os.makedirs(dst, exist_ok=True)
    out = []
    for f in files:
        shutil.copy2(f, os.path.join(dst, os.path.basename(f)))
        out.append(os.path.basename(f))
    return out


def load_overrides(ip: str) -> Dict[str, dict]:
    p = p_overrides(ip)
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_overrides(ip: str, ov: Dict[str, dict]):
    os.makedirs(os.path.dirname(p_overrides(ip)), exist_ok=True)
    with open(p_overrides(ip), "w", encoding="utf-8") as f:
        f.write("# 사람이 직접 지정한 기대값 (키: '시험ID|항목'). value=레지스터 값, image=IP 디렉토리 기준 이미지 경로\n")
        yaml.safe_dump(ov, f, allow_unicode=True, sort_keys=True)
