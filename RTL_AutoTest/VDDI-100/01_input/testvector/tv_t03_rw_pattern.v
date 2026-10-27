// @test T03 RW 패턴 쓰기/읽기
// VDDI-100 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t03_rw_pattern;
`include "vddi100_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'h0000);
    reg_read (ADDR_H_ACTIVE, 16'h0000, 16'hFFFF);   // pat=0x0000
    reg_write(ADDR_V_ACTIVE, 16'h0000);
    reg_read (ADDR_V_ACTIVE, 16'h0000, 16'hFFFF);   // pat=0x0000
    reg_write(ADDR_DISP_CTRL, 8'h00);
    reg_read (ADDR_DISP_CTRL, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_TPG_MODE, 8'h00);
    reg_read (ADDR_TPG_MODE, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_FG_R, 8'h00);
    reg_read (ADDR_FG_R, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_FG_G, 8'h00);
    reg_read (ADDR_FG_G, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_FG_B, 8'h00);
    reg_read (ADDR_FG_B, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_CHECKER_SZ, 8'h00);
    reg_read (ADDR_CHECKER_SZ, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_PIX_CTRL, 8'h00);
    reg_read (ADDR_PIX_CTRL, 8'h00, 8'hFF);   // pat=0x00
    reg_write(ADDR_SCRATCH, 16'h0000);
    reg_read (ADDR_SCRATCH, 16'h0000, 16'hFFFF);   // pat=0x0000
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'hFFFF);
    reg_read (ADDR_H_ACTIVE, 16'h07FF, 16'hFFFF);   // pat=0xFFFF
    reg_write(ADDR_V_ACTIVE, 16'hFFFF);
    reg_read (ADDR_V_ACTIVE, 16'h07FF, 16'hFFFF);   // pat=0xFFFF
    reg_write(ADDR_DISP_CTRL, 8'hFF);
    reg_read (ADDR_DISP_CTRL, 8'h03, 8'hFF);   // pat=0xFF
    reg_write(ADDR_TPG_MODE, 8'hFF);
    reg_read (ADDR_TPG_MODE, 8'h07, 8'hFF);   // pat=0xFF
    reg_write(ADDR_FG_R, 8'hFF);
    reg_read (ADDR_FG_R, 8'hFF, 8'hFF);   // pat=0xFF
    reg_write(ADDR_FG_G, 8'hFF);
    reg_read (ADDR_FG_G, 8'hFF, 8'hFF);   // pat=0xFF
    reg_write(ADDR_FG_B, 8'hFF);
    reg_read (ADDR_FG_B, 8'hFF, 8'hFF);   // pat=0xFF
    reg_write(ADDR_CHECKER_SZ, 8'hFF);
    reg_read (ADDR_CHECKER_SZ, 8'h07, 8'hFF);   // pat=0xFF
    reg_write(ADDR_PIX_CTRL, 8'hFF);
    reg_read (ADDR_PIX_CTRL, 8'h03, 8'hFF);   // pat=0xFF
    reg_write(ADDR_SCRATCH, 16'hFFFF);
    reg_read (ADDR_SCRATCH, 16'hFFFF, 16'hFFFF);   // pat=0xFFFF
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'h5555);
    reg_read (ADDR_H_ACTIVE, 16'h0555, 16'hFFFF);   // pat=0x5555
    reg_write(ADDR_V_ACTIVE, 16'h5555);
    reg_read (ADDR_V_ACTIVE, 16'h0555, 16'hFFFF);   // pat=0x5555
    reg_write(ADDR_DISP_CTRL, 8'h55);
    reg_read (ADDR_DISP_CTRL, 8'h01, 8'hFF);   // pat=0x55
    reg_write(ADDR_TPG_MODE, 8'h55);
    reg_read (ADDR_TPG_MODE, 8'h05, 8'hFF);   // pat=0x55
    reg_write(ADDR_FG_R, 8'h55);
    reg_read (ADDR_FG_R, 8'h55, 8'hFF);   // pat=0x55
    reg_write(ADDR_FG_G, 8'h55);
    reg_read (ADDR_FG_G, 8'h55, 8'hFF);   // pat=0x55
    reg_write(ADDR_FG_B, 8'h55);
    reg_read (ADDR_FG_B, 8'h55, 8'hFF);   // pat=0x55
    reg_write(ADDR_CHECKER_SZ, 8'h55);
    reg_read (ADDR_CHECKER_SZ, 8'h05, 8'hFF);   // pat=0x55
    reg_write(ADDR_PIX_CTRL, 8'h55);
    reg_read (ADDR_PIX_CTRL, 8'h01, 8'hFF);   // pat=0x55
    reg_write(ADDR_SCRATCH, 16'h5555);
    reg_read (ADDR_SCRATCH, 16'h5555, 16'hFFFF);   // pat=0x5555
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'hAAAA);
    reg_read (ADDR_H_ACTIVE, 16'h02AA, 16'hFFFF);   // pat=0xAAAA
    reg_write(ADDR_V_ACTIVE, 16'hAAAA);
    reg_read (ADDR_V_ACTIVE, 16'h02AA, 16'hFFFF);   // pat=0xAAAA
    reg_write(ADDR_DISP_CTRL, 8'hAA);
    reg_read (ADDR_DISP_CTRL, 8'h02, 8'hFF);   // pat=0xAA
    reg_write(ADDR_TPG_MODE, 8'hAA);
    reg_read (ADDR_TPG_MODE, 8'h02, 8'hFF);   // pat=0xAA
    reg_write(ADDR_FG_R, 8'hAA);
    reg_read (ADDR_FG_R, 8'hAA, 8'hFF);   // pat=0xAA
    reg_write(ADDR_FG_G, 8'hAA);
    reg_read (ADDR_FG_G, 8'hAA, 8'hFF);   // pat=0xAA
    reg_write(ADDR_FG_B, 8'hAA);
    reg_read (ADDR_FG_B, 8'hAA, 8'hFF);   // pat=0xAA
    reg_write(ADDR_CHECKER_SZ, 8'hAA);
    reg_read (ADDR_CHECKER_SZ, 8'h02, 8'hFF);   // pat=0xAA
    reg_write(ADDR_PIX_CTRL, 8'hAA);
    reg_read (ADDR_PIX_CTRL, 8'h02, 8'hFF);   // pat=0xAA
    reg_write(ADDR_SCRATCH, 16'hAAAA);
    reg_read (ADDR_SCRATCH, 16'hAAAA, 16'hFFFF);   // pat=0xAAAA
    $finish;
end
endmodule
