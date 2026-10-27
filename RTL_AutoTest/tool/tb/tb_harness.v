// Generic vector-driven test harness (tool side, not part of the IP).
// Files: tb_harness.v (명령 해석·프레임 캡처) / spi_master.vh / i2c_master.vh
// DUT port convention: clk, rst_n, if_sel, sclk, cs_n, mosi, miso, scl, sda_in, sda_oe, vs, de, r, g, b
// Compile with -DDUT_TOP=<top module name>
// Plusargs: +VEC=<file> +LOG=<file> +FRAME=<prefix> +IF=<0:SPI,1:I2C> +DEV=<i2c 7-bit addr, hex>
// Vector commands: RST | W <addr> <data> | R <addr> | F
`timescale 1ns/1ps
`ifndef DUT_TOP
`define DUT_TOP vddi_top
`endif
module tb_harness;
    localparam SCLK_HALF = 160;     // SPI 3.125 MHz
    localparam Q = 250;             // I2C quarter period -> SCL 1 MHz
    localparam FRAME_TIMEOUT = 2000000;

    reg clk = 0, rst_n = 0, if_sel = 0;
    reg sclk = 0, cs_n = 1, mosi = 0;
    reg scl = 1, m_sda_low = 0;
    wire miso, vs, de, sda_oe;
    wire [7:0] r, g, b;
    tri1 sda;                                   // pull-up
    assign sda = m_sda_low ? 1'b0 : 1'bz;
    assign sda = sda_oe    ? 1'b0 : 1'bz;
    always #20 clk = ~clk;                      // 25 MHz

    `DUT_TOP dut (
        .clk(clk), .rst_n(rst_n), .if_sel(if_sel),
        .sclk(sclk), .cs_n(cs_n), .mosi(mosi), .miso(miso),
        .scl(scl), .sda_in(sda), .sda_oe(sda_oe),
        .vs(vs), .de(de), .r(r), .g(g), .b(b)
    );

    integer fd_vec, fd_log, fd_frm, rc, frame_no, npix, timeout, ifm;
    reg [8*8-1:0] cmd;
    reg [8*256-1:0] vec_file, log_file, frame_prefix, frame_name;
    reg [7:0] a, d, rd;
    reg [6:0] dev;
    reg nack;

    // ------------------------------------------------------------ bus masters (분리된 파일)
    `include "spi_master.vh"
    `include "i2c_master.vh"

    // ------------------------------------------------------------ main
    initial begin
        if (!$value$plusargs("VEC=%s", vec_file))       vec_file = "vectors.txt";
        if (!$value$plusargs("LOG=%s", log_file))       log_file = "sim_log.txt";
        if (!$value$plusargs("FRAME=%s", frame_prefix)) frame_prefix = "frame";
        if (!$value$plusargs("IF=%d", ifm))             ifm = 0;
        if (!$value$plusargs("DEV=%h", dev))            dev = 7'h3C;
        if_sel = (ifm == 1);
        fd_vec = $fopen(vec_file, "r");
        fd_log = $fopen(log_file, "w");
        if (fd_vec == 0) begin $display("ERROR: cannot open vectors"); $finish; end
        frame_no = 0;
        rst_n = 0; repeat (5) @(posedge clk); rst_n = 1; repeat (5) @(posedge clk);

        while (!$feof(fd_vec)) begin
            rc = $fscanf(fd_vec, "%s", cmd);
            if (rc == 1) begin
                if (cmd == "RST") begin
                    rst_n = 0; repeat (5) @(posedge clk); rst_n = 1; repeat (5) @(posedge clk);
                end else if (cmd == "W") begin
                    rc = $fscanf(fd_vec, "%h %h", a, d);
                    if (if_sel) begin
                        i2c_write(a[6:0], d, nack);
                        if (nack) $fdisplay(fd_log, "W %02h NACK", a);
                    end else spi_xfer(1'b0, a[6:0], d, rd);
                end else if (cmd == "R") begin
                    rc = $fscanf(fd_vec, "%h", a);
                    nack = 0;
                    if (if_sel) i2c_read(a[6:0], rd, nack);
                    else        spi_xfer(1'b1, a[6:0], 8'h00, rd);
                    if (nack) $fdisplay(fd_log, "R %02h %02h NACK", a, rd);
                    else      $fdisplay(fd_log, "R %02h %02h", a, rd);
                end else if (cmd == "F") begin
                    $sformat(frame_name, "%0s_%0d.hex", frame_prefix, frame_no);
                    fd_frm = $fopen(frame_name, "w");
                    timeout = 0;
                    while (!(vs === 1'b1) && timeout < FRAME_TIMEOUT) begin
                        @(negedge clk); timeout = timeout + 1;
                    end
                    npix = 0;
                    if (timeout >= FRAME_TIMEOUT) begin
                        $fdisplay(fd_log, "F %0d TIMEOUT", frame_no);
                    end else begin
                        if (de) begin $fdisplay(fd_frm, "%02h%02h%02h", r, g, b); npix = npix + 1; end
                        @(negedge clk);
                        while (!(vs === 1'b1)) begin
                            if (de) begin $fdisplay(fd_frm, "%02h%02h%02h", r, g, b); npix = npix + 1; end
                            @(negedge clk);
                        end
                        $fdisplay(fd_log, "F %0d %0d", frame_no, npix);
                    end
                    $fclose(fd_frm);
                    frame_no = frame_no + 1;
                end
            end
        end
        $fclose(fd_vec);
        $fclose(fd_log);
        $finish;
    end
endmodule
