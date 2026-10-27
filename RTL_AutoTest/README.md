# RTL 테스트벡터 → SPI / I2C 변환 툴

**입력: 테스트벡터 RTL** (`reg_write / reg_read` 시퀀스) → **출력: SPI / I2C 테스트벡터 (Total Phase Aardvark Control Center 배치 XML)**.
변환한 각 줄이 원래 RTL의 몇 번째 줄에서 나왔는지 남겨, RTL ↔ 변환 결과를 서로 거슬러 확인할 수 있습니다.

실제 업무(퀄리타스반도체 검증지원실)에서 사양서 레지스터맵·SPI/I2C 프로토콜·업무 템플릿을 AI에 주고 만든 테스트벡터 변환·인가 툴을,
공개 가능한 **가상 디스플레이 구동 IC 2종**으로 재현했습니다.

> 회사에서 만든 툴과 칩 정보는 회사 자산이라 제출하지 않았습니다. IP, 사양서, 테스트벡터, 코드는 모두 이 과제를 위해 새로 만든 예시이며 방법론만 같습니다.

## 툴 본 기능 vs For Demo
| 구분 | 내용 | 위치 |
|---|---|---|
| **툴 본 기능** | 테스트벡터 RTL → (레지스터맵) → SPI / I2C 포맷 변환 | GUI 왼쪽, `03_vectors/` |
| **For Demo** | 실제로는 변환 벡터를 SPI/I2C 장비로 **실물 칩**에 인가한다. 시연 환경엔 칩이 없으므로 **칩의 RTL(demo_dut/)을 시뮬레이터에서 돌려** 같은 벡터를 파형 수준으로 인가·판정 | GUI 오른쪽 (주황색 FOR DEMO 표시, 툴바 체크박스로 숨기기 가능), `demo_dut/`, `04_results/` |

## AI 활용 원칙
1. **AI를 쓰기 전에 문제와 재원을 먼저 정리한다.** AI는 주어진 입력 안에서만 정확하다. 문제(테스트벡터를 장비 포맷으로 손으로 옮기다 생기는 실수)와 재원(테스트벡터 RTL, 레지스터 헤더, 사양서, 현장 지식)을 정리한 것이 AI의 입력이 된다. → `docs/00`
2. **AI 활용은 절차로 나눈다.** 단계마다 *입력 → AI 작업 → 사람 확인 → 통과 조건*을 정해, 통과한 산출물만 다음 단계로 넘긴다. 소스코드도 같은 단계로 나눠 단계별로 따로 실행·확인할 수 있게 했다. → `docs/01~04`, `tool/debug_stage.py`

| 단계 | AI 작업 | 사람 확인 | 통과 조건 | 소스 (tool/core) |
|---|---|---|---|---|
| 0 문제·재원 | - | 목표·완료 기준·재원·위험 정리 | 완료 기준 확정 | - |
| 1 레지스터맵 | 헤더 추출 코드 초안 | 사양서와 1:1 대조, IP별 수정 | "확인 필요" 0건 | rtl_parser, regmap |
| 2 파싱 | 테스트벡터 파서 초안 | 틀린 테스트벡터로 경고 확인 | 경고 0건 | tv_parser |
| 3 변환 | SPI/I2C 인코더 초안 | RTL 줄 ↔ 변환 줄 대응, 프레임 형식 대조 | 형식 일치 | vector_cmd, vector_spi, vector_i2c, vector_export |
| 4 Demo 인가 | 하네스·실행 코드 초안 | RTL 시뮬 결과와 Python 모델 교차 확인 | 두 결과 일치 | sim_runner, model_runner, tb/ |
| 5 Demo 판정 | 판정 코드 초안 | 일부러 틀린 조건으로 FAIL 확인 | 정상 PASS / 오류 FAIL | judge, endian_detect, golden_model |
| 환경 | 점검 스크립트 초안 | 설치 전 확인, 대체 경로 | 새 환경에서 실행 | run_tool |

## 폴더 구성
```
RTL_AutoTest/
├─ run_tool.bat / .ps1 / .sh        실행 (환경 점검·설치 → GUI), 실행방법.txt
├─ README.md
├─ docs/                            AI 활용 절차 문서
├─ VDDI-100/                        IP 작업공간 = IP 이름 디렉토리
│  ├─ 01_input/testvector/          ★ 입력: 테스트벡터 RTL (tv_t01~t07.v) + 레지스터 헤더 (vddi100_regmap.vh) + tv_tasks.vh
│  ├─ 01_input/spec/                사양서 (PDF)
│  ├─ 02_regmap/regmap.yaml         헤더에서 추출 → 검토 → 저장한 레지스터맵
│  ├─ 03_vectors/spi|i2c/           ★ 출력: Aardvark 배치 XML — 파일별 tv_*_spi.xml / _i2c.xml + all_spi.xml / all_i2c.xml
│  ├─ demo_dut/rtl/                 [For Demo] 실물 칩 대신 쓰는 DUT RTL
│  └─ 04_results/<실행>/            [For Demo] 인가·판정 리포트, debug/(시뮬레이터 원본 로그)
├─ VDDI-200/                        두 번째 예시 IP
└─ tool/                            툴 소스 전부
   ├─ run_tool.py · run_gui.py · cli.py
   ├─ debug_stage.py · self_check.py    단계별 디버그 / 자가 점검 (18항목)
   ├─ core/                         기능별 처리 모듈
   ├─ gui/                          화면 패널별 모듈
   ├─ tb/                           [For Demo] 하네스 + SPI/I2C 마스터
   └─ third_party/                  (선택) 포터블 Icarus Verilog 자리
```

예시 IP
| IP | 사양서 바이트 순서 | Demo 칩 실제 | CHIP_ID | I2C 주소 | 의도 |
|---|---|---|---|---|---|
| VDDI-100 | big | **little** | 0xD1A5 | 0x3C | 사양서와 칩이 다른 사례 → Demo에서 감지 |
| VDDI-200 | big | big | 0xD200 | 0x3D | 정상 사례, IP별 레지스터맵 차이 |

### tool/core 모듈
| 파일 | 하는 일 | 입력 → 출력 |
|---|---|---|
| workspace.py | IP 디렉토리 구조·생성·가져오기 | IP 이름 → 폴더 |
| rtl_parser.py | 레지스터 정의 헤더 파싱 | .vh → 레지스터 목록 + 정의 줄 |
| regmap.py | 레지스터맵 저장·검증, 바이트 순서 매핑 | regmap.yaml ↔ RegMap |
| tv_parser.py | **테스트벡터 RTL 파싱** | tv_*.v → 동작 (파일:줄 포함) |
| vector_cmd.py | 동작 → 바이트 단위 명령 | 바이트 순서 적용 |
| vector_aardvark.py | **Aardvark 배치 인코딩** (spi_write / i2c_write·i2c_read) | (주소, 데이터) → XML 명령 |
| vector_spi.py / vector_i2c.py | SPI 프레임 / I2C 시퀀스 표기 (수동 R/W 화면용) | |
| vector_export.py | **변환 파일 출력 + RTL 줄 대응표** | → 03_vectors |
| tv_writer.py | (보조) 시험 템플릿 → 예시 테스트벡터 RTL 생성 | testgen.py 사용 |
| sim_runner.py | [Demo] iverilog 컴파일·인가 | 명령 → RawResult |
| model_runner.py | [Demo] 시뮬레이터 없을 때 동작 모델 | 명령 → RawResult |
| golden_model.py / judge.py / endian_detect.py | [Demo] 기준 화면, 판정, 엔디안 감지 | RawResult → Result |
| report.py | [Demo] CSV / HTML 리포트 | → 04_results |
| pipeline.py | 단계 연결 (convert / run_demo) | GUI·CLI가 호출 |

## 실행
처음 보는 PC에서도 되도록 런처가 Python·패키지·권한을 점검하고 필요한 것을 설치합니다. 자세한 대체 방법은 `실행방법.txt`.

| 환경 | 기본 | 막혔을 때 |
|---|---|---|
| Windows | `run_tool.bat` 더블클릭 | `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_tool.ps1` → `py -3 tool\run_tool.py` |
| macOS / Linux | `./run_tool.sh` | `sh run_tool.sh` → `python3 tool/run_tool.py` |

- 점검: Python 3.9+ / 64bit, 폴더 쓰기 권한, 필수 파일·문법, tkinter, pip, pyyaml·pillow, PyPI 연결, iverilog, 자가 점검 18항목
- 설치(관리자 권한 불필요): Python 없으면 winget 사용자 설치 제안(Windows) / 패키지는 `tool/.venv` 가상환경 → `--user` → `tool/_pylibs` 순서로 시도
- 옵션: `--check-only`(점검만) `--full`(자가 점검 포함 후 GUI) `--yes`(묻지 않고 설치) `--cli`(GUI 없이)
- For Demo의 RTL 시뮬레이션은 Icarus Verilog 필요 (`tool/third_party/README.md`). 없으면 Python 모델로 자동 전환, **변환 기능은 시뮬레이터 없이 동작**

명령줄
```
python tool/cli.py extract --ip VDDI-100              # 헤더(.vh) -> 02_regmap/regmap.yaml
python tool/cli.py convert --ip VDDI-100 --if i2c     # 테스트벡터 RTL -> 03_vectors/i2c/   (본 기능)
python tool/cli.py demo    --ip VDDI-100 --if spi     # [For Demo] DUT RTL에 인가·판정
python tool/cli.py new     --ip MY_IP                 # IP 작업공간 생성
```

## GUI 사용 흐름
1. **IP 선택** (또는 새 IP 만들기 → 테스트벡터 가져오기)
2. **① 레지스터맵 추출** → 레지스터맵 탭에서 사양서와 대조·저장 (행 선택 → 정의 위치 보기)
3. **테스트벡터 RTL → SPI / I2C** 탭: 파일 클릭 → 왼쪽 RTL, 오른쪽 변환 결과. **RTL 줄 클릭 → 변환된 줄 강조**, 변환 줄 클릭 → RTL 줄로 이동
4. 툴바에서 출력 포맷(SPI / I2C), I2C 주소, 바이트 순서 선택 → 오른쪽 결과 즉시 갱신
5. **② SPI / I2C 변환** → `03_vectors/` 에 파일로 저장
6. (For Demo) **③ 인가·판정 실행** → DUT RTL에 인가, 결과·화면 비교·기대값 지정. 감지된 바이트 순서가 변환 설정과 다르면 다시 변환하라고 안내

## 시연 순서 (약 3분)
1. VDDI-100 → `tv_t03_rw_pattern.v` 선택 → `reg_write(ADDR_H_ACTIVE, 16'h0000)` 클릭 → SPI 2줄 강조 (16비트 = 바이트 2개)
2. 출력 포맷 I2C로 → 같은 줄이 `S 78 A 04 A 00 A P` 로 바뀜
3. ② 변환 → `03_vectors/i2c/` 파일 확인
4. For Demo: ③ 실행 (바이트 순서 사양서 값, 자동 감지 끔) → 115/139, 16비트만 FAIL
5. 자동 감지 켜고 실행 → "칩은 little" 감지 + "바이트 순서 바꿔 다시 변환" 안내 → 바꿔서 139/139
6. VDDI-200 → 다른 CHIP_ID·I2C 주소, 같은 방식으로 139/139
7. (질문 대비) `python tool/self_check.py` → 18/18, `debug_stage.py convert` 로 RTL 줄 ↔ 변환 줄 출력

## 디버깅
```
python tool/debug_stage.py extract --ip VDDI-100                     # 헤더 파싱
python tool/debug_stage.py regmap  --ip VDDI-100                     # 레지스터맵 + 바이트 배치
python tool/debug_stage.py parse   --ip VDDI-100 --test T05          # 테스트벡터 RTL 줄 -> 동작
python tool/debug_stage.py convert --ip VDDI-100 --if i2c --test T03 # RTL 줄 -> SPI/I2C 줄
python tool/debug_stage.py sim     --ip VDDI-100 --reg CHIP_ID       # [Demo] 레지스터 하나 인가
python tool/debug_stage.py judge   --ip VDDI-100 --order big         # [Demo] 판정 요약
python tool/self_check.py                                            # 전 단계 자가 점검
```

## DUT 포트 규약 (For Demo에 다른 칩 RTL을 넣을 때)
`clk, rst_n, if_sel(0:SPI 1:I2C), sclk, cs_n, mosi, miso, scl, sda_in, sda_oe, vs, de, r, g, b`

## 실제 업무 vs 이 재현에서 추가한 것
| 실제 업무에서 한 것 | 재현하며 추가한 것 |
|---|---|
| 사양서 레지스터맵·SPI/I2C 프로토콜·업무 템플릿을 AI에 주고 테스트벡터를 SPI/I2C로 변환·인가하는 Python GUI 제작 | RTL 줄 ↔ 변환 줄 추적, 실물 칩 대신 RTL 시뮬레이션(For Demo) |
| IP마다 엔디안이 다를 수 있다는 얘기를 듣고 바이트 순서 옵션 반영 | Demo에서 ID 레지스터로 바이트 순서 자동 감지 |
| PC마다 Python 버전이 다르다는 얘기를 듣고 버전·스크립트 확인 및 패키지 관리 프로그램 제작 | 시뮬레이터 동봉/대체 경로 |
| | 화면 출력 비교, 기대값 지정, 단계별 디버그·자가 점검 |

## 출력 형식: Aardvark 배치 (XML)
Total Phase Aardvark Control Center의 Batch 모드에서 불러오는 형식입니다.
```xml
<spi_write count="2" radix="16">84 00</spi_write>     <!-- 00003 L10 H_ACTIVE  expect 0x00 mask 0xFF -->
<i2c_write addr="0x3C" count="2" radix="16">04 40</i2c_write>              <!-- 쓰기: 레지스터 주소 + 데이터 -->
<i2c_write addr="0x3C" count="1" radix="16" nostop="1">04</i2c_write>      <!-- 읽기: 주소 설정, STOP 없음 -->
<i2c_read addr="0x3C" count="1"/>                                            <!--       repeated START 후 1바이트 -->
```
- SPI는 전이중이라 `spi_write` 하나로 쓰기와 MISO 수신이 동시에 일어남. 읽기 기대값·마스크는 주석에 표기 (자동 비교는 Python 쪽에서 수행)
- `chip_reset`은 레지스터 접근이 아닌 RST_N 핀 제어라 주석 + `<sleep>`으로 표시 (보드 GPIO / FPGA로 수행)
- 각 명령 주석의 `L<n>` = 원래 테스트벡터 RTL 줄 번호
- 태그·속성은 Control Center 배치 형식 기준. 사용하는 Control Center 버전과 다르면 `tool/core/vector_aardvark.py` 한 파일만 수정
