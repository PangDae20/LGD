// VDDI-100 top: host interface (SPI or I2C, selected by IF_SEL pin) + register bank + TPG
module vddi_top #(
    parameter ADDR_LE          = 1,
    parameter [15:0] CHIP_ID   = 16'hD1A5,
    parameter [6:0]  I2C_ADDR  = 7'h3C
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       if_sel,     // 0: SPI, 1: I2C
    // SPI
    input  wire       sclk,
    input  wire       cs_n,
    input  wire       mosi,
    output wire       miso,
    // I2C
    input  wire       scl,
    input  wire       sda_in,
    output wire       sda_oe,
    // pixel output
    output wire       vs,
    output wire       de,
    output wire [7:0] r, g, b
);
    wire        s_wr, i_wr;
    wire [6:0]  s_addr, i_addr;
    wire [7:0]  s_wdata, i_wdata, rdata;

    wire        wr_en = if_sel ? i_wr    : s_wr;
    wire [6:0]  addr  = if_sel ? i_addr  : s_addr;
    wire [7:0]  wdata = if_sel ? i_wdata : s_wdata;

    wire [10:0] h_active, v_active;
    wire        disp_active, invert, rb_swap;
    wire [2:0]  pattern, checker_sz;
    wire [7:0]  fg_r, fg_g, fg_b;

    spi_slave u_spi (
        .clk(clk), .rst_n(rst_n & ~if_sel), .sclk(sclk), .cs_n(cs_n), .mosi(mosi), .miso(miso),
        .wr_en(s_wr), .addr(s_addr), .wdata(s_wdata), .rdata(rdata)
    );

    i2c_slave #(.DEV_ADDR(I2C_ADDR)) u_i2c (
        .clk(clk), .rst_n(rst_n & if_sel), .scl(scl), .sda_in(sda_in), .sda_oe(sda_oe),
        .wr_en(i_wr), .addr(i_addr), .wdata(i_wdata), .rdata(rdata)
    );

    vddi_regs #(.ADDR_LE(ADDR_LE), .CHIP_ID_VAL(CHIP_ID)) u_regs (
        .clk(clk), .rst_n(rst_n), .wr_en(wr_en), .addr(addr), .wdata(wdata), .rdata(rdata),
        .h_active(h_active), .v_active(v_active), .disp_active(disp_active),
        .pattern(pattern), .fg_r(fg_r), .fg_g(fg_g), .fg_b(fg_b),
        .checker_sz(checker_sz), .invert(invert), .rb_swap(rb_swap)
    );

    vddi_tpg u_tpg (
        .clk(clk), .rst_n(rst_n), .enable(disp_active),
        .h_active(h_active), .v_active(v_active), .pattern(pattern),
        .fg_r(fg_r), .fg_g(fg_g), .fg_b(fg_b), .checker_sz(checker_sz),
        .invert(invert), .rb_swap(rb_swap),
        .vs(vs), .de(de), .r(r), .g(g), .b(b)
    );
endmodule
