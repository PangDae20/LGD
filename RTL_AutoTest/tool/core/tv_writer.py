"""[보조] 예시 입력 만들기: 시험 템플릿 -> 테스트벡터 RTL 파일 + 레지스터 정의 헤더.

실제 업무에서는 테스트벡터 RTL이 주어지는 입력이다. 이 파일은 예시 IP의 입력을 만들 때만 쓴다.
  python -m core.tv_writer <regmap.yaml> <template.yaml> <출력 폴더> [헤더 이름]
"""
import os
from typing import List

from .datatypes import TestCase
from .regmap import RegMap

TASKS_VH = """// tv_tasks.vh — 테스트벡터 RTL 공통 태스크
//   chip_reset;                          칩 리셋
//   reg_write(addr, data);               레지스터 쓰기 (레지스터 폭 단위)
//   reg_read (addr, expected, mask);     레지스터 읽기 + 기대값 비교 (mask 1인 비트만 비교)
//   frame_check("name");                 화면 1프레임 캡처 후 기준 모델과 비교
// 이 파일의 태스크는 형식 확인용 표시만 한다. 실제 인가는 툴이 SPI / I2C 포맷으로 변환해 수행.
task chip_reset;
    begin $display("RST"); end
endtask
task reg_write(input [7:0] addr, input [31:0] data);
    begin $display("W %02h %0h", addr, data); end
endtask
task reg_read(input [7:0] addr, input [31:0] exp, input [31:0] mask);
    begin $display("R %02h exp=%0h mask=%0h", addr, exp, mask); end
endtask
task frame_check(input [8*32-1:0] name);
    begin $display("F %0s", name); end
endtask
"""


def _lit(width: int, v: int) -> str:
    return f"{width}'h{v:0{max(width // 4, 2)}X}"


def regmap_header(rm: RegMap) -> str:
    out = [f"// {rm.name} register definitions — 설계/검증 공용 헤더 (사양서 4장 기준)",
           f"// 16-bit registers: {rm.spec_byte_order}-endian byte order (사양서 기재)",
           "// 형식: localparam ADDR_<이름> = <주소>; // REG width=.. access=.. reset=.. rw_mask=.. desc=\"..\""]
    for r in rm.regs:
        w = r.nbytes * 2
        vol = " volatile=1" if r.volatile else ""
        out.append(f"localparam [6:0] ADDR_{r.name:<11s}= 7'h{r.addr:02X}; // REG width={r.width:<2d} access={r.access} "
                   f"reset=0x{r.reset:0{w}X} rw_mask=0x{r.rw_mask:0{w}X} desc=\"{r.desc}\"{vol}")
    out.append(f"localparam [6:0] I2C_DEV_ADDR     = 7'h{rm.i2c_addr:02X}; // I2C 7-bit device address")
    return "\n".join(out) + "\n"


def tv_file(tc: TestCase, rm: RegMap, header: str, fname: str) -> str:
    mod = os.path.splitext(fname)[0]
    out = [f"// @test {tc.tid} {tc.desc}",
           f"// {rm.name} 테스트벡터 (RTL)",
           "`timescale 1ns/1ps",
           f"module {mod};",
           f"`include \"{header}\"",
           "`include \"tv_tasks.vh\"",
           "initial begin"]
    for op in tc.ops:
        if op.kind == "RST":
            out.append("    chip_reset;")
        elif op.kind == "WREG":
            r = rm[op.reg]
            out.append(f"    reg_write(ADDR_{r.name}, {_lit(r.width, op.value)});")
        elif op.kind == "RREG":
            r = rm[op.reg]
            line = f"    reg_read (ADDR_{r.name}, {_lit(r.width, op.value)}, {_lit(r.width, op.mask)});"
            out.append(line + (f"   // {op.label}" if op.label else ""))
        elif op.kind == "FRAME":
            out.append(f"    frame_check(\"{op.label}\");")
    out += ["    $finish;", "end", "endmodule"]
    return "\n".join(out) + "\n"


def write_all(cases: List[TestCase], rm: RegMap, out_dir: str, header: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, header), "w", encoding="utf-8") as f:
        f.write(regmap_header(rm))
    with open(os.path.join(out_dir, "tv_tasks.vh"), "w", encoding="utf-8") as f:
        f.write(TASKS_VH)
    names = []
    for tc in cases:
        fn = f"tv_{tc.tid.lower()}_{tc.ttype}.v"
        with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as f:
            f.write(tv_file(tc, rm, header, fn))
        names.append(fn)
    return names


if __name__ == "__main__":
    import sys
    from .testgen import generate
    rm = RegMap.load(sys.argv[1])
    hdr = sys.argv[4] if len(sys.argv) > 4 else f"{rm.name.lower().replace('-', '')}_regmap.vh"
    print(write_all(generate(rm, sys.argv[2]), rm, sys.argv[3], hdr))
