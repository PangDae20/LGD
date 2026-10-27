// SPI master tasks (Mode 0, MSB first, 16-bit frame [R/W|ADDR(7)|DATA(8)])
// included inside tb_harness. Uses: sclk, cs_n, mosi, miso, SCLK_HALF
    task spi_xfer(input rw, input [6:0] ad, input [7:0] wd, output [7:0] rdv);
        reg [15:0] frame; integer k;
        begin
            frame = {rw, ad, wd}; rdv = 0;
            cs_n = 0; #(SCLK_HALF);
            for (k = 15; k >= 0; k = k - 1) begin
                mosi = frame[k];
                #(SCLK_HALF) sclk = 1;
                if (k < 8) rdv = {rdv[6:0], miso};
                #(SCLK_HALF) sclk = 0;
            end
            #(SCLK_HALF) cs_n = 1; mosi = 0;
            #(SCLK_HALF*2);
        end
    endtask

