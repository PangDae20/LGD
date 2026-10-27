"""[3단계] I2C 시퀀스 인코딩.

7비트 장치 주소, 레지스터 포인터 1바이트
  쓰기: S | DEV+W | A | REG | A | DATA | A | P
  읽기: S | DEV+W | A | REG | A | Sr | DEV+R | A | DATA | NA | P
"""


def addr_byte(dev: int, read: bool) -> int:
    return ((dev & 0x7F) << 1) | (1 if read else 0)


def header(dev: int) -> list:
    return [f"# I2C 7-bit addr 0x{dev:02X} -> W=0x{addr_byte(dev, False):02X} R=0x{addr_byte(dev, True):02X}, "
            "A=ACK NA=NACK Sr=repeated START",
            "# idx  op  sequence                                    ; register / test"]


def encode_write(dev: int, addr: int, data: int) -> str:
    return f"W   S {addr_byte(dev, False):02X} A {addr:02X} A {data:02X} A P".ljust(47)


def encode_read(dev: int, addr: int, exp: int, mask: int) -> str:
    return (f"R   S {addr_byte(dev, False):02X} A {addr:02X} A Sr {addr_byte(dev, True):02X} A "
            f"[{exp:02X}&{mask:02X}] NA P").ljust(47)


def describe(dev: int, op: str, addr: int, data: int) -> str:
    """수동 R/W 화면 표시용"""
    if op == "W":
        return f"I2C S {addr_byte(dev, False):02X} A {addr:02X} A {data:02X} A P"
    return f"I2C S {addr_byte(dev, False):02X} A {addr:02X} A Sr {addr_byte(dev, True):02X} A [{data:02X}] NA P"


if __name__ == "__main__":
    print(encode_write(0x3C, 0x04, 0x40))
    print(encode_read(0x3C, 0x00, 0xD1, 0xFF))
