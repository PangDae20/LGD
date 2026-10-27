// @test T05 RO 쓰기 보호
// VDDI-200 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t05_ro_protect;
`include "vddi200_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_write(ADDR_CHIP_ID, 16'h2DFF);
    reg_read (ADDR_CHIP_ID, 16'hD200, 16'hFFFF);   // write ~reset
    reg_write(ADDR_REV_ID, 8'hEF);
    reg_read (ADDR_REV_ID, 8'h10, 8'hFF);   // write ~reset
    $finish;
end
endmodule
