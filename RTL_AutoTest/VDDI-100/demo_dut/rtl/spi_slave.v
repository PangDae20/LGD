// SPI slave, Mode 0 (CPOL=0, CPHA=0), MSB first
// Frame: [15] R/W (1=read) [14:8] ADDR [7:0] DATA, one byte per CS_N assertion.
// SCLK/CS_N/MOSI are oversampled by the system clock (clk >= 4x SCLK).
module spi_slave (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       sclk,
    input  wire       cs_n,
    input  wire       mosi,
    output reg        miso,
    // register bank interface
    output reg        wr_en,
    output reg  [6:0] addr,
    output reg  [7:0] wdata,
    input  wire [7:0] rdata      // combinational read of 'addr'
);
    // 2-FF synchronizers
    reg [2:0] sclk_s, cs_s;
    reg [1:0] mosi_s;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sclk_s <= 3'b000; cs_s <= 3'b111; mosi_s <= 2'b00;
        end else begin
            sclk_s <= {sclk_s[1:0], sclk};
            cs_s   <= {cs_s[1:0],   cs_n};
            mosi_s <= {mosi_s[0],   mosi};
        end
    end
    wire sclk_rise = (sclk_s[2:1] == 2'b01);
    wire sclk_fall = (sclk_s[2:1] == 2'b10);
    wire cs_active = ~cs_s[1];
    wire mosi_b    = mosi_s[1];

    reg [4:0] bit_cnt;
    reg [7:0] shreg;
    reg       is_read;
    reg [7:0] tx;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bit_cnt <= 0; shreg <= 0; is_read <= 0; tx <= 0;
            addr <= 0; wdata <= 0; wr_en <= 0; miso <= 0;
        end else begin
            wr_en <= 1'b0;
            if (!cs_active) begin
                bit_cnt <= 0;
                miso    <= 1'b0;
            end else begin
                if (sclk_rise) begin
                    shreg   <= {shreg[6:0], mosi_b};
                    bit_cnt <= bit_cnt + 1'b1;
                    if (bit_cnt == 5'd7) begin
                        // header complete: {R/W, ADDR}
                        is_read <= shreg[6];
                        addr    <= {shreg[5:0], mosi_b};
                    end
                    if (bit_cnt == 5'd15 && !is_read) begin
                        wdata <= {shreg[6:0], mosi_b};
                        wr_en <= 1'b1;
                    end
                end
                if (sclk_fall) begin
                    if (bit_cnt == 5'd8) begin
                        // first data bit must be on MISO before the 9th rising edge
                        tx   <= {rdata[6:0], 1'b0};
                        miso <= is_read ? rdata[7] : 1'b0;
                    end else if (bit_cnt > 5'd8 && bit_cnt < 5'd16) begin
                        miso <= is_read ? tx[7] : 1'b0;
                        tx   <= {tx[6:0], 1'b0};
                    end
                end
            end
        end
    end
endmodule
