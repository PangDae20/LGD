"""자가 점검 — 기능을 바꾼 뒤 각 단계가 여전히 맞게 동작하는지 한 번에 확인.

  python tool/self_check.py          (iverilog 없으면 시뮬레이션 항목은 건너뜀)

각 항목은 [단계] 이름 -> PASS / FAIL 로 출력되고, 실패하면 어느 모듈을 볼지 표시한다.
04_results 에는 아무것도 쓰지 않는다 (임시 파일은 각 IP의 .work/).
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_PYLIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pylibs")  # run_tool.py 의 대체 설치 위치
if os.path.isdir(_PYLIBS):
    sys.path.insert(0, _PYLIBS)

from core import vector_i2c, vector_spi, workspace as ws  # noqa: E402
from core.datatypes import RawResult  # noqa: E402
from core.endian_detect import detect_byte_order  # noqa: E402
from core.golden_model import tpg_frame  # noqa: E402
from core.judge import judge  # noqa: E402
from core.pipeline import load_cases, load_regmap, make_backend  # noqa: E402
from core.rtl_parser import extract  # noqa: E402
from core.sim_runner import find_iverilog  # noqa: E402
from core.tv_parser import parse_number  # noqa: E402
from core.vector_cmd import serialize  # noqa: E402
from core.vector_export import export_with_map  # noqa: E402

IP100 = os.path.join(ws.PROJECT_ROOT, "VDDI-100")
IP200 = os.path.join(ws.PROJECT_ROOT, "VDDI-200")
HAS_SIM = find_iverilog() is not None
results = []


def check(stage, name, module):
    def deco(fn):
        try:
            msg = fn()
            if msg == "SKIP":
                results.append((stage, name, "SKIP", "", module))
            else:
                results.append((stage, name, "PASS", msg or "", module))
        except AssertionError as e:
            results.append((stage, name, "FAIL", str(e), module))
        except Exception:
            results.append((stage, name, "FAIL", traceback.format_exc().strip().splitlines()[-1], module))
        return fn
    return deco


def run_case(ip, iface, order, backend, i2c_addr=None):
    rm = load_regmap(ip)
    be = make_backend(backend, rm, ip, iface, rm.i2c_addr if i2c_addr is None else i2c_addr)
    cases, _ = load_cases(ip, rm)
    res = judge(cases, rm, order, be.run(serialize(cases, rm, order), lambda m: None))
    return res


@check("1 추출", "헤더(.vh)에서 레지스터 13개·I2C 주소", "core/rtl_parser.py")
def _():
    h, regs, warns = extract([os.path.join(IP100, f) for f in ws.list_tv_headers(IP100)], IP100)
    assert len(regs) == 13, f"레지스터 수 {len(regs)}"
    assert h.get("i2c_addr") == 0x3C, str(h)
    assert not [w for w in warns if "확인 필요" in w], "속성 누락 경고"


@check("1 추출", "레지스터맵 파일 검증 (두 IP)", "core/regmap.py")
def _():
    for ip in (IP100, IP200):
        load_regmap(ip).validate()


@check("1 추출", "바이트 순서 매핑 (16비트 레지스터)", "core/regmap.py:byte_lanes")
def _():
    rm = load_regmap(IP100)
    r = rm["H_ACTIVE"]
    assert rm.split(r, 0x0140, "big") == [(0x04, 0x01), (0x05, 0x40)]
    assert rm.split(r, 0x0140, "little") == [(0x04, 0x40), (0x05, 0x01)]
    assert rm.join(r, {4: 0x40, 5: 0x01}, "little") == 0x0140


@check("2 파싱", "Verilog 숫자 해석", "core/tv_parser.py:parse_number")
def _():
    assert parse_number("16'h0040") == 0x40 and parse_number("8'b1010") == 10
    assert parse_number("96") == 96 and parse_number("'hFF") == 0xFF


@check("2 파싱", "테스트벡터 RTL 7개 -> 시험 T01~T07, 기대값·RTL 위치", "core/tv_parser.py")
def _():
    rm = load_regmap(IP100)
    cases, warns = load_cases(IP100, rm)
    assert [c.tid for c in cases] == ["T01", "T02", "T03", "T04", "T05", "T06", "T07"], [c.tid for c in cases]
    assert not warns, warns[0]
    t02 = cases[1]
    exp = {op.reg: op.value for op in t02.ops if op.kind == "RREG"}
    assert exp["CHIP_ID"] == 0xD1A5 and exp["H_ACTIVE"] == 0x40
    assert all(op.src.startswith("01_input/testvector/") for op in t02.ops)


@check("3 변환", "RTL 한 줄(16비트 쓰기) -> Aardvark spi_write 2줄, 같은 RTL 위치", "core/vector_export.py")
def _():
    rm = load_regmap(IP100)
    cases, _ = load_cases(IP100, rm)
    t03 = cases[2]
    wop = next(op for op in t03.ops if op.kind == "WREG" and op.reg == "H_ACTIVE")
    lines, srcs = export_with_map([t03], rm, "big", "spi", 0x3C, header=False)
    hit = [ln for ln, s_ in zip(lines, srcs) if s_ == wop.src]
    assert len(hit) == 2 and ">04 00</spi_write>" in hit[0] and ">05 00</spi_write>" in hit[1], hit


@check("3 변환", "SPI 프레임 비트 배치", "core/vector_spi.py")
def _():
    assert vector_spi.frame(0, 0x04, 0x40) == 0x0440
    assert vector_spi.frame(1, 0x00) == 0x8000


@check("3 변환", "I2C 장치 주소 바이트", "core/vector_i2c.py")
def _():
    assert vector_i2c.addr_byte(0x3C, False) == 0x78 and vector_i2c.addr_byte(0x3C, True) == 0x79


@check("5 Demo", "기준 모델 컬러바 (첫 막대 흰색, 마지막 검정)", "core/golden_model.py")
def _():
    st = {"H_ACTIVE": 64, "V_ACTIVE": 2, "TPG_MODE": 1, "FG_R": 0, "FG_G": 0, "FG_B": 0, "CHECKER_SZ": 3, "PIX_CTRL": 0}
    w, h, px = tpg_frame(st)
    assert (w, h) == (64, 2) and px[0] == (255, 255, 255) and px[63] == (0, 0, 0)


@check("5 Demo", "판정 로직: 바이트가 뒤집히면 엔디안 표시", "core/judge.py")
def _():
    rm = load_regmap(IP100)
    from core.datatypes import Op, TestCase
    tc = TestCase("X", "x", "x", [Op("RST"), Op("RREG", "CHIP_ID", 0xD1A5, 0xFFFF)])
    res = judge([tc], rm, "big", RawResult(reads=[(0, 0xA5, False), (1, 0xD1, False)]))[0]
    assert not res.passed and "엔디안" in res.note


@check("4 Demo", "Python 모델: VDDI-100 자동 감지 순서로 전부 PASS", "core/model_runner.py")
def _():
    res = run_case(IP100, "spi", "little", "model")
    n = sum(r.passed for r in res)
    assert n == len(res), f"{n}/{len(res)}"
    return f"{n}/{len(res)}"


for iface in ("spi", "i2c"):
    @check("4 Demo", f"RTL {iface.upper()}: VDDI-100 little 순서 전부 PASS", f"core/sim_runner.py, tb/{iface}_master.vh")
    def _(iface=iface):
        if not HAS_SIM:
            return "SKIP"
        res = run_case(IP100, iface, "little", "sim")
        n = sum(r.passed for r in res)
        assert n == len(res), f"{n}/{len(res)}"
        return f"{n}/{len(res)}"

    @check("4 Demo", f"RTL {iface.upper()}: 사양서 순서(big)면 16비트만 FAIL (115/139)", "core/judge.py")
    def _(iface=iface):
        if not HAS_SIM:
            return "SKIP"
        res = run_case(IP100, iface, "big", "sim")
        n = sum(r.passed for r in res)
        assert n == 115, f"{n}/{len(res)}"
        return f"{n}/{len(res)}"


@check("4 Demo", "RTL 시뮬레이션과 Python 모델 판정 일치", "core/sim_runner.py vs core/model_runner.py")
def _():
    if not HAS_SIM:
        return "SKIP"
    a = [(r.key, r.passed, r.actual) for r in run_case(IP100, "spi", "big", "sim")]
    b = [(r.key, r.passed, r.actual) for r in run_case(IP100, "spi", "big", "model")]
    diff = [x for x, y in zip(a, b) if x != y]
    assert not diff, f"{len(diff)}개 다름, 첫 항목 {diff[0]}"


@check("5 Demo", "엔디안 자동 감지: VDDI-100 little / VDDI-200 big", "core/endian_detect.py")
def _():
    kind = "sim" if HAS_SIM else "model"
    for ip, want in ((IP100, "little"), (IP200, "big")):
        rm = load_regmap(ip)
        got, msg = detect_byte_order(make_backend(kind, rm, ip, "spi", rm.i2c_addr), rm, lambda m: None)
        assert got == want, f"{os.path.basename(ip)}: {got} ({msg})"


@check("4 Demo", "I2C 장치 주소가 틀리면 NACK", "core/sim_runner.py, tb/i2c_master.vh")
def _():
    if not HAS_SIM:
        return "SKIP"
    rm = load_regmap(IP200)
    got, msg = detect_byte_order(make_backend("sim", rm, IP200, "i2c", 0x3C), rm, lambda m: None)
    assert "NACK" in msg, msg


if __name__ == "__main__":
    print(f"iverilog: {'있음' if HAS_SIM else '없음 (시뮬레이션 항목 SKIP)'}\n")
    for stage, name, st, msg, mod in results:
        line = f"[{st:4s}] {stage:6s} {name}" + (f"  ({msg})" if msg else "")
        print(line)
        if st == "FAIL":
            print(f"         -> 확인할 곳: {mod}")
    nfail = sum(1 for r in results if r[2] == "FAIL")
    print(f"\n{len(results) - nfail}/{len(results)} 통과" + ("" if not nfail else f", {nfail}건 실패"))
    sys.exit(1 if nfail else 0)
