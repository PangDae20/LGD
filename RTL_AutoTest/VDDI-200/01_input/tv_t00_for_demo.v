// @test T00 for_demo / 시연을 위한 임의 값 읽기/쓰기
// VDDI-200 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t00_for_demo;
`include "vddi200_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;

    // ---- [1] ID 확인 : 값을 아는 16비트 레지스터로 바이트 순서 확인
    reg_read (ADDR_CHIP_ID, 16'hD200, 16'hFFFF);    // ID 0xD200 (big: 0x00=D2, 0x01=00)
    reg_read (ADDR_REV_ID,  8'h10,    8'hFF);       // REV 0x10

    // ---- [2] 헤더 주소(기호)로 쓰기/읽기 : 8비트
    reg_write(ADDR_FG_R, 8'h5A);
    reg_read (ADDR_FG_R, 8'h5A, 8'hFF);             // FG_R 0x5A
    reg_write(ADDR_FG_G, 8'hA5);
    reg_read (ADDR_FG_G, 8'hA5, 8'hFF);             // FG_G 0xA5

    // ---- [3] 주소 직접 입력(숫자)으로 쓰기/읽기 : 헤더 기호와 같은 레지스터로 해석됨
    reg_write(7'h0C, 8'h3C);                        // 0x0C = FG_B
    reg_read (7'h0C, 8'h3C, 8'hFF);                 // FG_B 0x3C (addr 7'h0C)
    reg_write(7'h09, 8'h05);                        // 0x09 = TPG_MODE
    reg_read (7'h09, 8'h05, 8'h07);                 // TPG_MODE 0x05 (addr 7'h09)

    // ---- [4] 엔디안 : 16비트 레지스터에 상·하위 바이트가 다른 값
    reg_write(ADDR_SCRATCH, 16'h1234);              // big: 0x10=12, 0x11=34 / little: 0x10=34, 0x11=12
    reg_read (ADDR_SCRATCH, 16'h1234, 16'hFFFF);    // SCRATCH 0x1234
    reg_write(7'h10, 16'hBEEF);                     // 주소 직접 입력 + 16비트
    reg_read (7'h10, 16'hBEEF, 16'hFFFF);           // SCRATCH 0xBEEF (addr 7'h10)
    reg_write(ADDR_H_ACTIVE, 16'h0280);             // 640 pixels
    reg_read (ADDR_H_ACTIVE, 16'h0280, 16'h07FF);   // H_ACTIVE 640

    // ---- [5] 쓰기 가능 비트(rw_mask) : 쓰지 않는 비트는 0으로 읽힘
    reg_write(ADDR_V_ACTIVE, 16'hFFFF);
    reg_read (ADDR_V_ACTIVE, 16'h07FF, 16'hFFFF);   // V_ACTIVE [10:0]만 저장
    reg_write(ADDR_PIX_CTRL, 8'hFF);
    reg_read (ADDR_PIX_CTRL, 8'h03, 8'hFF);         // PIX_CTRL [1:0]만 저장

    // ---- [6] 읽기 전용(RO) : 써도 값이 바뀌지 않음
    reg_write(ADDR_REV_ID, 8'hFF);
    reg_read (ADDR_REV_ID, 8'h10, 8'hFF);           // REV_ID 쓰기 무시

    // ---- [7] 툴 입력 검사 : 변환 시 '파싱 경고' 칸에 표시
    reg_write(ADDR_FG_R, 16'h01C3);                 // 8비트 초과 -> 하위 8비트(0xC3)만 사용
    reg_read (ADDR_FG_R, 8'hC3, 8'hFF);             // FG_R 0xC3
    reg_write(7'h20, 8'h11);                        // 레지스터맵에 없는 주소 -> 변환에서 제외

    // ---- [8] 리셋 후 기본값 복귀
    chip_reset;
    reg_read (ADDR_SCRATCH, 16'h0000, 16'hFFFF);    // SCRATCH reset 0x0000
    reg_read (7'h0A, 8'hFF, 8'hFF);                 // FG_R reset 0xFF (addr 7'h0A)

    $finish;
end
endmodule
