"""[3단계] SPI 프레임 인코딩.

Mode 0, MSB first, 16비트 프레임 = [R/W(1) | ADDR(7) | DATA(8)]
R/W = 0 쓰기, 1 읽기 (읽기 때 DATA 자리는 0, MISO로 데이터가 나옴)
"""


def frame(rw: int, addr: int, data: int = 0) -> int:
    return ((rw & 1) << 15) | ((addr & 0x7F) << 8) | (data & 0xFF)


def header() -> list:
    return ["# SPI Mode 0 (CPOL=0, CPHA=0), MSB first, 16-bit frame = [R/W | ADDR(7) | DATA(8)]",
            "# idx  op  MOSI    MISO_exp  mask  ; register / test"]


def encode_write(addr: int, data: int) -> str:
    return f"W   0x{frame(0, addr, data):04X}  -         -   "


def encode_read(addr: int, exp: int, mask: int) -> str:
    return f"R   0x{frame(1, addr):04X}  0x{exp:02X}      0x{mask:02X}"


def describe(op: str, addr: int, data: int) -> str:
    """수동 R/W 화면 표시용"""
    if op == "W":
        return f"SPI MOSI 0x{frame(0, addr, data):04X}  (R/W=0, ADDR=0x{addr:02X}, DATA=0x{data:02X})"
    return f"SPI MOSI 0x{frame(1, addr):04X} -> MISO 0x{data:02X}"


if __name__ == "__main__":
    # 디버그: 프레임 비트 배치 확인
    for op, a, d in (("W", 0x04, 0x40), ("R", 0x00, 0)):
        f = frame(op == "R", a, d)
        print(f"{op} addr=0x{a:02X} data=0x{d:02X} -> 0x{f:04X} = {f:016b}")
