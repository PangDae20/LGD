// VDDI-200 Test Pattern Generator: 1 pixel per clock
module vddi_tpg (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        enable,
    input  wire [10:0] h_active,
    input  wire [10:0] v_active,
    input  wire [2:0]  pattern,
    input  wire [7:0]  fg_r, fg_g, fg_b,
    input  wire [2:0]  checker_sz,
    input  wire        invert,
    input  wire        rb_swap,
    output reg         vs,
    output reg         de,
    output reg  [7:0]  r, g, b
);
    localparam HBLANK = 8;
    localparam VBLANK = 2;

    reg [11:0] x, y;
    reg [10:0] bar_cnt;   // pixel count inside current color bar
    reg [2:0]  bar_idx;

    wire [10:0] bw_raw = h_active >> 3;
    wire [10:0] bw     = (bw_raw == 0) ? 11'd1 : bw_raw;
    wire [11:0] h_tot  = h_active + HBLANK;
    wire [11:0] v_tot  = v_active + VBLANK;
    wire        active = (x < h_active) && (y < v_active);

    // ---- pattern (combinational on current x, y) ----
    reg [7:0] pr, pg, pb;
    reg [7:0] ramp;
    reg       chk_on;
    always @(*) begin
        ramp = {x[5:0], 2'b00};                       // (x*4) mod 256
        chk_on = ((x >> checker_sz) ^ (y >> checker_sz)) & 1'b1;
        case (pattern)
            3'd0: begin pr = fg_r; pg = fg_g; pb = fg_b; end
            3'd1: case (bar_idx)                      // W Y C G M R B K
                    3'd0: begin pr=8'hFF; pg=8'hFF; pb=8'hFF; end
                    3'd1: begin pr=8'hFF; pg=8'hFF; pb=8'h00; end
                    3'd2: begin pr=8'h00; pg=8'hFF; pb=8'hFF; end
                    3'd3: begin pr=8'h00; pg=8'hFF; pb=8'h00; end
                    3'd4: begin pr=8'hFF; pg=8'h00; pb=8'hFF; end
                    3'd5: begin pr=8'hFF; pg=8'h00; pb=8'h00; end
                    3'd6: begin pr=8'h00; pg=8'h00; pb=8'hFF; end
                    default: begin pr=8'h00; pg=8'h00; pb=8'h00; end
                  endcase
            3'd2: begin pr = ramp & fg_r; pg = ramp & fg_g; pb = ramp & fg_b; end
            3'd3: begin
                    pr = chk_on ? fg_r : 8'h00;
                    pg = chk_on ? fg_g : 8'h00;
                    pb = chk_on ? fg_b : 8'h00;
                  end
            default: begin pr = 8'h00; pg = 8'h00; pb = 8'h00; end
        endcase
    end

    // post processing: RB swap, then invert
    wire [7:0] sr = rb_swap ? pb : pr;
    wire [7:0] sb = rb_swap ? pr : pb;
    wire [7:0] or_ = invert ? ~sr : sr;
    wire [7:0] og  = invert ? ~pg : pg;
    wire [7:0] ob  = invert ? ~sb : sb;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x <= 0; y <= 0; bar_cnt <= 0; bar_idx <= 0;
            vs <= 0; de <= 0; r <= 0; g <= 0; b <= 0;
        end else if (!enable) begin
            x <= 0; y <= 0; bar_cnt <= 0; bar_idx <= 0;
            vs <= 0; de <= 0;
        end else begin
            // registered pixel output
            vs <= (x == 0) && (y == 0);
            de <= active;
            r  <= active ? or_ : 8'h00;
            g  <= active ? og  : 8'h00;
            b  <= active ? ob  : 8'h00;

            // color bar index tracking
            if (x == h_tot - 1) begin
                bar_cnt <= 0; bar_idx <= 0;
            end else if (bar_cnt == bw - 1) begin
                bar_cnt <= 0;
                if (bar_idx != 3'd7) bar_idx <= bar_idx + 1'b1;
            end else begin
                bar_cnt <= bar_cnt + 1'b1;
            end

            // raster counters
            if (x == h_tot - 1) begin
                x <= 0;
                y <= (y == v_tot - 1) ? 12'd0 : y + 1'b1;
            end else begin
                x <= x + 1'b1;
            end
        end
    end
endmodule
