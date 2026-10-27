// @test T07 테스트패턴 출력 비교
// VDDI-100 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t07_functional;
`include "vddi100_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h01);
    reg_write(ADDR_DISP_CTRL, 8'h03);
    frame_check("colorbar");
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h02);
    reg_write(ADDR_FG_R, 8'hFF);
    reg_write(ADDR_FG_G, 8'h00);
    reg_write(ADDR_FG_B, 8'h00);
    reg_write(ADDR_DISP_CTRL, 8'h03);
    frame_check("ramp_red");
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h03);
    reg_write(ADDR_CHECKER_SZ, 8'h02);
    reg_write(ADDR_FG_R, 8'h20);
    reg_write(ADDR_FG_G, 8'hC0);
    reg_write(ADDR_FG_B, 8'hFF);
    reg_write(ADDR_DISP_CTRL, 8'h03);
    frame_check("checker_4px");
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h01);
    reg_write(ADDR_PIX_CTRL, 8'h03);
    reg_write(ADDR_DISP_CTRL, 8'h03);
    frame_check("colorbar_swap_inv");
    chip_reset;
    reg_write(ADDR_TPG_MODE, 8'h00);
    reg_write(ADDR_H_ACTIVE, 16'h0060);
    reg_write(ADDR_V_ACTIVE, 16'h0036);
    reg_write(ADDR_FG_R, 8'h40);
    reg_write(ADDR_FG_G, 8'h80);
    reg_write(ADDR_FG_B, 8'hC0);
    reg_write(ADDR_DISP_CTRL, 8'h03);
    frame_check("solid_96x54");
    $finish;
end
endmodule
