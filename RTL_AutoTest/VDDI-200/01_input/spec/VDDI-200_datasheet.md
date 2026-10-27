# VDDI-200 Display Driver IC — Register Interface Specification

Rev 1.0 · 가상 디바이스 (테스트 자동화 툴 시연용 예시 IP)

## 1. Overview

VDDI-200은 디스플레이 구동 IC의 제어부를 단순화한 예시 IP다.
호스트 인터페이스(SPI 또는 I2C), 바이트 주소 레지스터 뱅크, 패널 출력용
테스트 패턴 생성기(TPG, Test Pattern Generator)로 구성된다.

| 구성 | 역할 |
|---|---|
| Host I/F | SPI 슬레이브 또는 I2C 슬레이브 (IF_SEL 핀으로 선택) |
| Register Bank | 바이트 주소 레지스터 13개 |
| TPG | 레지스터 설정에 따라 VS / DE / RGB 출력 |

데이터 흐름: 호스트(SPI/I2C) → Host I/F → Register Bank → TPG → 패널 출력

## 2. Pin Description

| Pin | Dir | Description |
|---|---|---|
| CLK | I | 시스템 클럭 25 MHz |
| RST_N | I | 비동기 리셋, Low active |
| IF_SEL | I | 호스트 인터페이스 선택 (0: SPI, 1: I2C) |
| SCLK, CS_N, MOSI | I | SPI |
| MISO | O | SPI |
| SCL | I | I2C 클럭 |
| SDA | I/O | I2C 데이터 (open-drain, 외부 pull-up) |
| VS, DE | O | 프레임 시작, 유효 픽셀 |
| R, G, B [7:0] | O | 픽셀 데이터 |

## 3. Host Interface

두 인터페이스 모두 같은 레지스터 뱅크에 접근한다. 한 트랜잭션에 1바이트를 전송한다.

### 3.1 SPI

| Item | Value |
|---|---|
| Mode | Mode 0 (CPOL = 0, CPHA = 0) |
| Bit order | MSB first |
| Chip select | CS_N, active low |
| Frame | 16 SCLK = header 1 byte + data 1 byte |
| Max SCLK | 6 MHz (CLK/4) |

```
 bit:   15   14 ........ 8   7 ............ 0
       R/W  ADDR[6:0]        DATA[7:0]
```
* R/W = 0: write, R/W = 1: read (DATA는 MISO로 출력, bit 7..0 구간)

### 3.2 I2C

| Item | Value |
|---|---|
| Device address (7-bit) | **0x3D** |
| Speed | Standard / Fast / Fast-mode Plus (최대 1 MHz) |
| Register pointer | 1 byte, 데이터 바이트마다 자동 증가 |

```
Write : S | 0x3D+W | A | REG | A | DATA | A | P
Read  : S | 0x3D+W | A | REG | A | Sr | 0x3D+R | A | DATA | NA | P
```
* 장치 주소가 다르면 ACK를 보내지 않는다 (NACK).

## 4. Register Map

모든 주소는 바이트 주소이다.
**16비트 레지스터는 big-endian 바이트 순서로 저장된다 (낮은 주소 = bits [15:8]).**

| Addr | Name | Width | Access | Reset | Description |
|---|---|---|---|---|---|
| 0x00 | CHIP_ID | 16 | RO | 0xD200 | Device ID |
| 0x02 | REV_ID | 8 | RO | 0x10 | Silicon revision |
| 0x03 | STATUS | 8 | RO | 0x00 | [0] DISP_ACTIVE (= DISP_ON & TPG_EN), [7:1] reserved |
| 0x04 | H_ACTIVE | 16 | RW | 0x0040 | [10:0] 가로 유효 픽셀 수, [15:11] reserved |
| 0x06 | V_ACTIVE | 16 | RW | 0x0030 | [10:0] 세로 유효 라인 수, [15:11] reserved |
| 0x08 | DISP_CTRL | 8 | RW | 0x00 | [0] DISP_ON, [1] TPG_EN, [7:2] reserved |
| 0x09 | TPG_MODE | 8 | RW | 0x01 | [2:0] PATTERN, [7:3] reserved |
| 0x0A | FG_R | 8 | RW | 0xFF | 전경색 R |
| 0x0B | FG_G | 8 | RW | 0xFF | 전경색 G |
| 0x0C | FG_B | 8 | RW | 0xFF | 전경색 B |
| 0x0D | CHECKER_SZ | 8 | RW | 0x03 | [2:0] 체커 셀 크기 log2, [7:3] reserved |
| 0x0E | PIX_CTRL | 8 | RW | 0x00 | [0] INVERT, [1] RB_SWAP, [7:2] reserved |
| 0x10 | SCRATCH | 16 | RW | 0x0000 | 범용 레지스터 |

* reserved 비트는 0으로 읽히며, 쓰기는 무시된다.
* RO 레지스터 쓰기는 무시된다. 정의되지 않은 주소는 0x00으로 읽힌다.

## 5. Test Pattern Generator

STATUS.DISP_ACTIVE = 1일 때 동작. x = 0..H_ACTIVE−1, y = 0..V_ACTIVE−1.

| PATTERN | Name | Pixel (R, G, B) |
|---|---|---|
| 0 | Solid | (FG_R, FG_G, FG_B) |
| 1 | Color bar | 8개 세로 막대, 폭 bw = max(H_ACTIVE >> 3, 1), 막대 번호 = min(x / bw, 7). 순서: 흰, 노, 청록, 초, 자홍, 빨, 파, 검 |
| 2 | Ramp | v = (x × 4) mod 256, 픽셀 = (v & FG_R, v & FG_G, v & FG_B) |
| 3 | Checker | c = ((x >> n) XOR (y >> n)) & 1, n = CHECKER_SZ; c = 1이면 FG, 0이면 검정 |
| 4–7 | Reserved | 검정 |

후처리 순서: RB_SWAP(R과 B 교환) → INVERT(각 채널 255 − 값).

타이밍: 라인당 H_ACTIVE 픽셀 + 블랭킹 8클럭, 프레임당 V_ACTIVE 라인 + 블랭킹 2라인.
VS는 프레임 첫 픽셀에서 1클럭 High.
