# third_party — 동봉 도구

## Icarus Verilog (포터블)
설치 권한이 없거나 Icarus Verilog가 없는 PC에서도 RTL 시뮬레이션이 되도록, 툴이 이 폴더를 가장 먼저 찾는다.
(찾는 순서: 이 폴더 → PATH → C:\iverilog\bin. 모두 없으면 Python 모델로 자동 전환)

```
third_party/iverilog/
  bin/iverilog.exe, vvp.exe, (필요한 dll)
  lib/ivl/...            <- bin 과 같은 상위 폴더 아래에 그대로 둘 것 (vvp가 상대 경로로 찾음)
  COPYING                <- GPL 라이선스 문서 (재배포 시 함께 포함)
```

넣는 방법 (Windows)
1. https://bleyer.org/icarus/ 에서 설치 파일을 받아 아무 경로에 설치 (GTKWave 선택 해제하면 용량 감소)
2. 설치된 폴더(예: C:\iverilog)의 `bin`, `lib` 폴더와 라이선스 파일을 여기 `iverilog/` 아래로 복사
3. 원래 설치 폴더 이름을 잠시 바꾼 뒤 `python tool/run_tool.py --check-only` 실행 →
   "iverilog 출처: 동봉판" 이 나오면 정상

Icarus Verilog: GPL-2.0, https://github.com/steveicarus/iverilog
