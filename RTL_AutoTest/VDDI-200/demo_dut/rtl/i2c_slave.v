// I2C slave (7-bit device address), oversampled by the system clock (clk >= 20x SCL).
// Write : S | DEV+W | A | REG | A | DATA | A | ... | P      (register pointer auto-increments)
// Read  : S | DEV+W | A | REG | A | Sr | DEV+R | A | DATA | NA | P
// SDA is open-drain: sda_oe = 1 pulls the line low.
module i2c_slave #(
    parameter [6:0] DEV_ADDR = 7'h3C
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       scl,
    input  wire       sda_in,
    output reg        sda_oe,
    output reg        wr_en,
    output reg  [6:0] addr,
    output reg  [7:0] wdata,
    input  wire [7:0] rdata          // combinational read of 'addr'
);
    // synchronizers
    reg [2:0] scl_s, sda_s;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin scl_s <= 3'b111; sda_s <= 3'b111; end
        else begin scl_s <= {scl_s[1:0], scl}; sda_s <= {sda_s[1:0], sda_in}; end
    end
    wire scl_rise = (scl_s[2:1] == 2'b01);
    wire scl_fall = (scl_s[2:1] == 2'b10);
    wire scl_hi   = scl_s[1];
    wire sda_b    = sda_s[1];
    wire start    = scl_hi & scl_s[2] & (sda_s[2:1] == 2'b10);   // SDA falls while SCL high
    wire stop     = scl_hi & scl_s[2] & (sda_s[2:1] == 2'b01);   // SDA rises while SCL high

    localparam S_IDLE = 3'd0, S_DEV = 3'd1, S_REG = 3'd2, S_WDATA = 3'd3, S_RDATA = 3'd4;
    reg [2:0] state, next_state;
    reg [3:0] bit_cnt;
    reg [7:0] shreg, tx;
    reg       ack_phase;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_IDLE; next_state <= S_IDLE; bit_cnt <= 0; shreg <= 0; tx <= 0;
            ack_phase <= 0; sda_oe <= 0; wr_en <= 0; addr <= 0; wdata <= 0;
        end else begin
            wr_en <= 1'b0;
            if (start) begin
                state <= S_DEV; bit_cnt <= 0; ack_phase <= 0; sda_oe <= 0;
            end else if (stop) begin
                state <= S_IDLE; ack_phase <= 0; sda_oe <= 0;
            end else case (state)
                S_DEV, S_REG, S_WDATA: begin
                    if (scl_rise && !ack_phase && bit_cnt < 8) begin
                        shreg   <= {shreg[6:0], sda_b};
                        bit_cnt <= bit_cnt + 1'b1;
                    end
                    if (scl_fall && !ack_phase && bit_cnt == 8) begin
                        // 8 bits received: decide ACK and next state
                        if (state == S_DEV) begin
                            if (shreg[7:1] == DEV_ADDR) begin
                                sda_oe <= 1'b1; ack_phase <= 1'b1;
                                next_state <= shreg[0] ? S_RDATA : S_REG;
                            end else begin
                                state <= S_IDLE;            // not addressed: no ACK
                            end
                        end else if (state == S_REG) begin
                            addr <= shreg[6:0];
                            sda_oe <= 1'b1; ack_phase <= 1'b1; next_state <= S_WDATA;
                        end else begin
                            wdata <= shreg; wr_en <= 1'b1;
                            sda_oe <= 1'b1; ack_phase <= 1'b1; next_state <= S_WDATA;
                        end
                    end else if (scl_fall && ack_phase) begin
                        // end of ACK clock: release SDA
                        ack_phase <= 1'b0; bit_cnt <= 0; sda_oe <= 1'b0;
                        state <= next_state;
                        if (state == S_WDATA) addr <= addr + 1'b1;   // auto-increment after a data byte
                        if (next_state == S_RDATA) begin
                            sda_oe <= ~rdata[7];
                            tx     <= {rdata[6:0], 1'b0};
                        end
                    end
                end
                S_RDATA: begin
                    if (scl_rise) bit_cnt <= bit_cnt + 1'b1;
                    if (scl_fall) begin
                        if (bit_cnt >= 1 && bit_cnt <= 7) begin
                            sda_oe <= ~tx[7];
                            tx     <= {tx[6:0], 1'b0};
                        end else if (bit_cnt == 8) begin
                            sda_oe <= 1'b0;               // release for master ACK/NACK
                        end else if (bit_cnt == 9) begin
                            state <= S_IDLE;              // single-byte read; wait for STOP / Sr
                        end
                    end
                end
                default: ;
            endcase
        end
    end
endmodule
