// tv_tasks.vh — 테스트벡터 RTL 공통 태스크
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
