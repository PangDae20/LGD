// @test T01 Chip ID / 바이트 순서 확인
// VDDI-100 테스트벡터 (RTL)
`timescale 1ns/1ps
module tv_t01_id_check;
`include "vddi100_regmap.vh"
`include "tv_tasks.vh"
initial begin
    chip_reset;
    reg_read (ADDR_CHIP_ID, 16'hD1A5, 16'hFFFF);   // ID
    $finish;
end
endmodule
