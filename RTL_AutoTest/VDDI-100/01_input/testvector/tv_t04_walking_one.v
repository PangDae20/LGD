// @test T04 Walking-1
// VDDI-100 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t04_walking_one;
`include "vddi100_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_write(ADDR_H_ACTIVE, 16'h0001);
    reg_read (ADDR_H_ACTIVE, 16'h0001, 16'hFFFF);   // bit0
    reg_write(ADDR_H_ACTIVE, 16'h0002);
    reg_read (ADDR_H_ACTIVE, 16'h0002, 16'hFFFF);   // bit1
    reg_write(ADDR_H_ACTIVE, 16'h0004);
    reg_read (ADDR_H_ACTIVE, 16'h0004, 16'hFFFF);   // bit2
    reg_write(ADDR_H_ACTIVE, 16'h0008);
    reg_read (ADDR_H_ACTIVE, 16'h0008, 16'hFFFF);   // bit3
    reg_write(ADDR_H_ACTIVE, 16'h0010);
    reg_read (ADDR_H_ACTIVE, 16'h0010, 16'hFFFF);   // bit4
    reg_write(ADDR_H_ACTIVE, 16'h0020);
    reg_read (ADDR_H_ACTIVE, 16'h0020, 16'hFFFF);   // bit5
    reg_write(ADDR_H_ACTIVE, 16'h0040);
    reg_read (ADDR_H_ACTIVE, 16'h0040, 16'hFFFF);   // bit6
    reg_write(ADDR_H_ACTIVE, 16'h0080);
    reg_read (ADDR_H_ACTIVE, 16'h0080, 16'hFFFF);   // bit7
    reg_write(ADDR_H_ACTIVE, 16'h0100);
    reg_read (ADDR_H_ACTIVE, 16'h0100, 16'hFFFF);   // bit8
    reg_write(ADDR_H_ACTIVE, 16'h0200);
    reg_read (ADDR_H_ACTIVE, 16'h0200, 16'hFFFF);   // bit9
    reg_write(ADDR_H_ACTIVE, 16'h0400);
    reg_read (ADDR_H_ACTIVE, 16'h0400, 16'hFFFF);   // bit10
    chip_reset;
    reg_write(ADDR_V_ACTIVE, 16'h0001);
    reg_read (ADDR_V_ACTIVE, 16'h0001, 16'hFFFF);   // bit0
    reg_write(ADDR_V_ACTIVE, 16'h0002);
    reg_read (ADDR_V_ACTIVE, 16'h0002, 16'hFFFF);   // bit1
    reg_write(ADDR_V_ACTIVE, 16'h0004);
    reg_read (ADDR_V_ACTIVE, 16'h0004, 16'hFFFF);   // bit2
    reg_write(ADDR_V_ACTIVE, 16'h0008);
    reg_read (ADDR_V_ACTIVE, 16'h0008, 16'hFFFF);   // bit3
    reg_write(ADDR_V_ACTIVE, 16'h0010);
    reg_read (ADDR_V_ACTIVE, 16'h0010, 16'hFFFF);   // bit4
    reg_write(ADDR_V_ACTIVE, 16'h0020);
    reg_read (ADDR_V_ACTIVE, 16'h0020, 16'hFFFF);   // bit5
    reg_write(ADDR_V_ACTIVE, 16'h0040);
    reg_read (ADDR_V_ACTIVE, 16'h0040, 16'hFFFF);   // bit6
    reg_write(ADDR_V_ACTIVE, 16'h0080);
    reg_read (ADDR_V_ACTIVE, 16'h0080, 16'hFFFF);   // bit7
    reg_write(ADDR_V_ACTIVE, 16'h0100);
    reg_read (ADDR_V_ACTIVE, 16'h0100, 16'hFFFF);   // bit8
    reg_write(ADDR_V_ACTIVE, 16'h0200);
    reg_read (ADDR_V_ACTIVE, 16'h0200, 16'hFFFF);   // bit9
    reg_write(ADDR_V_ACTIVE, 16'h0400);
    reg_read (ADDR_V_ACTIVE, 16'h0400, 16'hFFFF);   // bit10
    chip_reset;
    reg_write(ADDR_DISP_CTRL, 8'h01);
    reg_read (ADDR_DISP_CTRL, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_DISP_CTRL, 8'h02);
    reg_read (ADDR_DISP_CTRL, 8'h02, 8'hFF);   // bit1
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h01);
    reg_read (ADDR_TPG_MODE, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_TPG_MODE, 8'h02);
    reg_read (ADDR_TPG_MODE, 8'h02, 8'hFF);   // bit1
    reg_write(ADDR_TPG_MODE, 8'h04);
    reg_read (ADDR_TPG_MODE, 8'h04, 8'hFF);   // bit2
    chip_reset;
    reg_write(ADDR_FG_R, 8'h01);
    reg_read (ADDR_FG_R, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_FG_R, 8'h02);
    reg_read (ADDR_FG_R, 8'h02, 8'hFF);   // bit1
    reg_write(ADDR_FG_R, 8'h04);
    reg_read (ADDR_FG_R, 8'h04, 8'hFF);   // bit2
    reg_write(ADDR_FG_R, 8'h08);
    reg_read (ADDR_FG_R, 8'h08, 8'hFF);   // bit3
    reg_write(ADDR_FG_R, 8'h10);
    reg_read (ADDR_FG_R, 8'h10, 8'hFF);   // bit4
    reg_write(ADDR_FG_R, 8'h20);
    reg_read (ADDR_FG_R, 8'h20, 8'hFF);   // bit5
    reg_write(ADDR_FG_R, 8'h40);
    reg_read (ADDR_FG_R, 8'h40, 8'hFF);   // bit6
    reg_write(ADDR_FG_R, 8'h80);
    reg_read (ADDR_FG_R, 8'h80, 8'hFF);   // bit7
    chip_reset;
    reg_write(ADDR_FG_G, 8'h01);
    reg_read (ADDR_FG_G, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_FG_G, 8'h02);
    reg_read (ADDR_FG_G, 8'h02, 8'hFF);   // bit1
    reg_write(ADDR_FG_G, 8'h04);
    reg_read (ADDR_FG_G, 8'h04, 8'hFF);   // bit2
    reg_write(ADDR_FG_G, 8'h08);
    reg_read (ADDR_FG_G, 8'h08, 8'hFF);   // bit3
    reg_write(ADDR_FG_G, 8'h10);
    reg_read (ADDR_FG_G, 8'h10, 8'hFF);   // bit4
    reg_write(ADDR_FG_G, 8'h20);
    reg_read (ADDR_FG_G, 8'h20, 8'hFF);   // bit5
    reg_write(ADDR_FG_G, 8'h40);
    reg_read (ADDR_FG_G, 8'h40, 8'hFF);   // bit6
    reg_write(ADDR_FG_G, 8'h80);
    reg_read (ADDR_FG_G, 8'h80, 8'hFF);   // bit7
    chip_reset;
    reg_write(ADDR_FG_B, 8'h01);
    reg_read (ADDR_FG_B, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_FG_B, 8'h02);
    reg_read (ADDR_FG_B, 8'h02, 8'hFF);   // bit1
    reg_write(ADDR_FG_B, 8'h04);
    reg_read (ADDR_FG_B, 8'h04, 8'hFF);   // bit2
    reg_write(ADDR_FG_B, 8'h08);
    reg_read (ADDR_FG_B, 8'h08, 8'hFF);   // bit3
    reg_write(ADDR_FG_B, 8'h10);
    reg_read (ADDR_FG_B, 8'h10, 8'hFF);   // bit4
    reg_write(ADDR_FG_B, 8'h20);
    reg_read (ADDR_FG_B, 8'h20, 8'hFF);   // bit5
    reg_write(ADDR_FG_B, 8'h40);
    reg_read (ADDR_FG_B, 8'h40, 8'hFF);   // bit6
    reg_write(ADDR_FG_B, 8'h80);
    reg_read (ADDR_FG_B, 8'h80, 8'hFF);   // bit7
    chip_reset;
    reg_write(ADDR_CHECKER_SZ, 8'h01);
    reg_read (ADDR_CHECKER_SZ, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_CHECKER_SZ, 8'h02);
    reg_read (ADDR_CHECKER_SZ, 8'h02, 8'hFF);   // bit1
    reg_write(ADDR_CHECKER_SZ, 8'h04);
    reg_read (ADDR_CHECKER_SZ, 8'h04, 8'hFF);   // bit2
    chip_reset;
    reg_write(ADDR_PIX_CTRL, 8'h01);
    reg_read (ADDR_PIX_CTRL, 8'h01, 8'hFF);   // bit0
    reg_write(ADDR_PIX_CTRL, 8'h02);
    reg_read (ADDR_PIX_CTRL, 8'h02, 8'hFF);   // bit1
    chip_reset;
    reg_write(ADDR_SCRATCH, 16'h0001);
    reg_read (ADDR_SCRATCH, 16'h0001, 16'hFFFF);   // bit0
    reg_write(ADDR_SCRATCH, 16'h0002);
    reg_read (ADDR_SCRATCH, 16'h0002, 16'hFFFF);   // bit1
    reg_write(ADDR_SCRATCH, 16'h0004);
    reg_read (ADDR_SCRATCH, 16'h0004, 16'hFFFF);   // bit2
    reg_write(ADDR_SCRATCH, 16'h0008);
    reg_read (ADDR_SCRATCH, 16'h0008, 16'hFFFF);   // bit3
    reg_write(ADDR_SCRATCH, 16'h0010);
    reg_read (ADDR_SCRATCH, 16'h0010, 16'hFFFF);   // bit4
    reg_write(ADDR_SCRATCH, 16'h0020);
    reg_read (ADDR_SCRATCH, 16'h0020, 16'hFFFF);   // bit5
    reg_write(ADDR_SCRATCH, 16'h0040);
    reg_read (ADDR_SCRATCH, 16'h0040, 16'hFFFF);   // bit6
    reg_write(ADDR_SCRATCH, 16'h0080);
    reg_read (ADDR_SCRATCH, 16'h0080, 16'hFFFF);   // bit7
    reg_write(ADDR_SCRATCH, 16'h0100);
    reg_read (ADDR_SCRATCH, 16'h0100, 16'hFFFF);   // bit8
    reg_write(ADDR_SCRATCH, 16'h0200);
    reg_read (ADDR_SCRATCH, 16'h0200, 16'hFFFF);   // bit9
    reg_write(ADDR_SCRATCH, 16'h0400);
    reg_read (ADDR_SCRATCH, 16'h0400, 16'hFFFF);   // bit10
    reg_write(ADDR_SCRATCH, 16'h0800);
    reg_read (ADDR_SCRATCH, 16'h0800, 16'hFFFF);   // bit11
    reg_write(ADDR_SCRATCH, 16'h1000);
    reg_read (ADDR_SCRATCH, 16'h1000, 16'hFFFF);   // bit12
    reg_write(ADDR_SCRATCH, 16'h2000);
    reg_read (ADDR_SCRATCH, 16'h2000, 16'hFFFF);   // bit13
    reg_write(ADDR_SCRATCH, 16'h4000);
    reg_read (ADDR_SCRATCH, 16'h4000, 16'hFFFF);   // bit14
    reg_write(ADDR_SCRATCH, 16'h8000);
    reg_read (ADDR_SCRATCH, 16'h8000, 16'hFFFF);   // bit15
    $finish;
end
endmodule
