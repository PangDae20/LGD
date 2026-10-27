"""RTL 레지스터 자동 시험 툴 — 기능별 모듈

처리 순서와 담당 파일 (각 단계는 tool/debug_stage.py 로 따로 실행해 중간 결과 확인 가능)

  [작업공간]  workspace.py      IP 디렉토리 구조(01_input ~ 04_results), 경로, 생성
  [1 추출]    rtl_parser.py     RTL -> 레지스터 정의 초안
              regmap.py         레지스터맵 저장/검증, 바이트 순서(엔디안) 매핑
  [2 시험]    testgen.py        템플릿 + 레지스터맵 -> 레지스터 단위 시험 동작
  [3 벡터]    vector_cmd.py     시험 동작 -> 하네스 명령(바이트 단위)
              vector_spi.py     SPI 프레임 인코딩
              vector_i2c.py     I2C 시퀀스 인코딩
              vector_export.py  인터페이스별 벡터 파일 출력
  [4 인가]    sim_runner.py     iverilog로 RTL 컴파일·인가 (SPI/I2C 파형 수준)
              model_runner.py   시뮬레이터 없을 때 Python 동작 모델
  [5 판정]    golden_model.py   화면 출력 기준 모델
              judge.py          기대값 비교, 기대값 지정 반영
              endian_detect.py  ID 레지스터로 실제 바이트 순서 판단
  [6 결과]    report.py         CSV / HTML 리포트
  [전체]      pipeline.py       위 단계를 순서대로 연결
  [공통]      datatypes.py      단계 사이에 주고받는 자료형
"""
