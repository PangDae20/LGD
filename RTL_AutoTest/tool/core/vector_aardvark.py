"""[3단계] Total Phase Aardvark (I2C/SPI Host Adapter) — Control Center 배치(XML) 인코딩.

Control Center 의 Batch 모드에서 불러와 바로 실행하는 형식으로 출력한다.
  SPI : 16비트 프레임 = 2바이트 [R/W|ADDR(7)] [DATA(8)]  ->  <spi_write count="2" radix="16">84 00</spi_write>
        SPI 는 전이중이라 spi_write 하나가 쓰기와 읽기(MISO 수신)를 동시에 함. 읽기 기대값은 주석으로 표기
  I2C : 쓰기  <i2c_write addr="0x3C" count="2" radix="16">04 40</i2c_write>
        읽기  <i2c_write ... nostop="1">04</i2c_write> (레지스터 포인터, STOP 없음 -> repeated START)
              <i2c_read addr="0x3C" count="1"/>
  리셋(chip_reset) : 레지스터 접근이 아니라 RST_N 핀 제어라서 주석 + 대기로 표시 (보드 GPIO/FPGA로 수행)
  화면 캡처(frame_check) : DSO 측정 지점 주석
각 동작 줄 끝 주석에 원래 테스트벡터 RTL 줄 번호(L<n>)를 남긴다.
"""


def _hex(bs):
    return " ".join("{:02X}".format(b) for b in bs)


def header(iface: str, dev: int, name: str, order: str) -> list:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           "<!-- {} test vectors : Aardvark Control Center batch  interface={}  byte_order={} -->"
           .format(name, iface.upper(), order),
           "<aardvark>"]
    if iface == "spi":
        out += ['  <configure i2c="0" spi="1" gpio="0" tpower="1" pullups="0"/>',
                '  <spi_config polarity="rising/falling" phase="sample/setup" bitorder="msb" ss="active_low"/>',
                '  <spi_bitrate khz="1000"/>',
                "  <!-- SPI Mode 0, MSB first, frame = [R/W|ADDR(7)] [DATA(8)] -->"]
    else:
        out += ['  <configure i2c="1" spi="0" gpio="0" tpower="1" pullups="1"/>',
                '  <i2c_bitrate khz="400"/>',
                "  <!-- I2C 7-bit device address 0x{:02X} -->".format(dev)]
    return out


def footer() -> list:
    return ["</aardvark>"]


def spi_write(addr: int, data: int) -> str:
    return '<spi_write count="2" radix="16">{}</spi_write>'.format(_hex([addr & 0x7F, data & 0xFF]))


def spi_read(addr: int) -> str:
    return '<spi_write count="2" radix="16">{}</spi_write>'.format(_hex([0x80 | (addr & 0x7F), 0x00]))


def i2c_write(dev: int, addr: int, data: int) -> list:
    return ['<i2c_write addr="0x{:02X}" count="2" radix="16">{}</i2c_write>'.format(dev, _hex([addr, data]))]


def i2c_read(dev: int, addr: int) -> list:
    return ['<i2c_write addr="0x{:02X}" count="1" radix="16" nostop="1">{}</i2c_write>'.format(dev, _hex([addr])),
            '<i2c_read addr="0x{:02X}" count="1"/>'.format(dev)]


def reset() -> list:
    return ["<!-- chip_reset : RST_N low -> high (board GPIO / FPGA) -->", '<sleep ms="10"/>']


def capture(name: str) -> list:
    return ["<!-- frame_check '{}' : DSO capture / compare -->".format(name)]


def comment(text: str) -> str:
    return "<!-- {} -->".format(text.replace("--", "-"))
