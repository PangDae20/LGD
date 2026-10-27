// @test T06 예약 비트 확인
// VDDI-200 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t06_reserved_bits;
`include "vddi200_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'hFFFF);
    reg_read (ADDR_H_ACTIVE, 16'h07FF, 16'hFFFF);   // write all-1
    reg_write(ADDR_V_ACTIVE, 16'hFFFF);
    reg_read (ADDR_V_ACTIVE, 16'h07FF, 16'hFFFF);   // write all-1
    reg_write(ADDR_DISP_CTRL, 8'hFF);
    reg_read (ADDR_DISP_CTRL, 8'h03, 8'hFF);   // write all-1
    reg_write(ADDR_TPG_MODE, 8'hFF);
    reg_read (ADDR_TPG_MODE, 8'h07, 8'hFF);   // write all-1
    reg_write(ADDR_CHECKER_SZ, 8'hFF);
    reg_read (ADDR_CHECKER_SZ, 8'h07, 8'hFF);   // write all-1
    reg_write(ADDR_PIX_CTRL, 8'hFF);
    reg_read (ADDR_PIX_CTRL, 8'h03, 8'hFF);   // write all-1
    $finish;
end
endmodule
