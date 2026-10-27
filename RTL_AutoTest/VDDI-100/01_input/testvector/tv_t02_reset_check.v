// @test T02 리셋값 확인
// VDDI-100 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t02_reset_check;
`include "vddi100_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_read (ADDR_CHIP_ID, 16'hD1A5, 16'hFFFF);   // reset
    reg_read (ADDR_REV_ID, 8'h10, 8'hFF);   // reset
    reg_read (ADDR_STATUS, 8'h00, 8'hFF);   // reset
    reg_read (ADDR_H_ACTIVE, 16'h0040, 16'hFFFF);   // reset
    reg_read (ADDR_V_ACTIVE, 16'h0030, 16'hFFFF);   // reset
    reg_read (ADDR_DISP_CTRL, 8'h00, 8'hFF);   // reset
    reg_read (ADDR_TPG_MODE, 8'h01, 8'hFF);   // reset
    reg_read (ADDR_FG_R, 8'hFF, 8'hFF);   // reset
    reg_read (ADDR_FG_G, 8'hFF, 8'hFF);   // reset
    reg_read (ADDR_FG_B, 8'hFF, 8'hFF);   // reset
    reg_read (ADDR_CHECKER_SZ, 8'h03, 8'hFF);   // reset
    reg_read (ADDR_PIX_CTRL, 8'h00, 8'hFF);   // reset
    reg_read (ADDR_SCRATCH, 16'h0000, 16'hFFFF);   // reset
    $finish;
end
endmodule
