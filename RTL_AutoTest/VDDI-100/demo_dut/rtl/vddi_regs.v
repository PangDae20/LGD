// VDDI-100 byte-addressed register bank
// Register definitions: one localparam per register (ADDR_<NAME>),
// attributes in the trailing "// REG" comment.
module vddi_regs #(
    parameter ADDR_LE     = 1,          // 1: 16-bit regs little-endian (lower addr = [7:0]), 0: big-endian
    parameter [15:0] CHIP_ID_VAL = 16'hD1A5,
    parameter [7:0]  REV_ID_VAL  = 8'h10
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        wr_en,
    input  wire [6:0]  addr,
    input  wire [7:0]  wdata,
    output reg  [7:0]  rdata,
    output reg  [10:0] h_active,
    output reg  [10:0] v_active,
    output wire        disp_active,
    output reg  [2:0]  pattern,
    output reg  [7:0]  fg_r, fg_g, fg_b,
    output reg  [2:0]  checker_sz,
    output reg         invert,
    output reg         rb_swap
);
    // ---------------------------------------------------------------- register map
    localparam [6:0] ADDR_CHIP_ID    = 7'h00; // REG width=16 access=RO reset=0xD1A5 rw_mask=0x0000 desc="Device ID"
    localparam [6:0] ADDR_REV_ID     = 7'h02; // REG width=8  access=RO reset=0x10   rw_mask=0x00   desc="Silicon revision"
    localparam [6:0] ADDR_STATUS     = 7'h03; // REG width=8  access=RO reset=0x00   rw_mask=0x00   desc="[0] DISP_ACTIVE" volatile=1
    localparam [6:0] ADDR_H_ACTIVE   = 7'h04; // REG width=16 access=RW reset=0x0040 rw_mask=0x07FF desc="[10:0] H active pixels"
    localparam [6:0] ADDR_V_ACTIVE   = 7'h06; // REG width=16 access=RW reset=0x0030 rw_mask=0x07FF desc="[10:0] V active lines"
    localparam [6:0] ADDR_DISP_CTRL  = 7'h08; // REG width=8  access=RW reset=0x00   rw_mask=0x03   desc="[0] DISP_ON [1] TPG_EN"
    localparam [6:0] ADDR_TPG_MODE   = 7'h09; // REG width=8  access=RW reset=0x01   rw_mask=0x07   desc="[2:0] PATTERN"
    localparam [6:0] ADDR_FG_R       = 7'h0A; // REG width=8  access=RW reset=0xFF   rw_mask=0xFF   desc="Foreground R"
    localparam [6:0] ADDR_FG_G       = 7'h0B; // REG width=8  access=RW reset=0xFF   rw_mask=0xFF   desc="Foreground G"
    localparam [6:0] ADDR_FG_B       = 7'h0C; // REG width=8  access=RW reset=0xFF   rw_mask=0xFF   desc="Foreground B"
    localparam [6:0] ADDR_CHECKER_SZ = 7'h0D; // REG width=8  access=RW reset=0x03   rw_mask=0x07   desc="[2:0] log2 cell size"
    localparam [6:0] ADDR_PIX_CTRL   = 7'h0E; // REG width=8  access=RW reset=0x00   rw_mask=0x03   desc="[0] INVERT [1] RB_SWAP"
    localparam [6:0] ADDR_SCRATCH    = 7'h10; // REG width=16 access=RW reset=0x0000 rw_mask=0xFFFF desc="Scratch"

    reg [1:0]  disp_ctrl;
    reg [15:0] scratch;
    assign disp_active = disp_ctrl[0] & disp_ctrl[1];

    // byte lane of a 16-bit register (even base address)
    wire odd     = addr[0];
    wire hi_lane = ADDR_LE ? odd : ~odd;     // 1: this byte address carries [15:8]
    wire [6:0] base = {addr[6:1], 1'b0};

    // ---------------- write ----------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            h_active   <= 11'd64;
            v_active   <= 11'd48;
            disp_ctrl  <= 2'b00;
            pattern    <= 3'd1;
            fg_r <= 8'hFF; fg_g <= 8'hFF; fg_b <= 8'hFF;
            checker_sz <= 3'd3;
            invert     <= 1'b0;
            rb_swap    <= 1'b0;
            scratch    <= 16'h0000;
        end else if (wr_en) begin
            if (base == ADDR_H_ACTIVE) begin
                if (hi_lane) h_active[10:8] <= wdata[2:0]; else h_active[7:0] <= wdata;
            end else if (base == ADDR_V_ACTIVE) begin
                if (hi_lane) v_active[10:8] <= wdata[2:0]; else v_active[7:0] <= wdata;
            end else if (base == ADDR_SCRATCH) begin
                if (hi_lane) scratch[15:8]  <= wdata;      else scratch[7:0]  <= wdata;
            end else begin
                case (addr)
                    ADDR_DISP_CTRL:  disp_ctrl  <= wdata[1:0];
                    ADDR_TPG_MODE:   pattern    <= wdata[2:0];
                    ADDR_FG_R:       fg_r       <= wdata;
                    ADDR_FG_G:       fg_g       <= wdata;
                    ADDR_FG_B:       fg_b       <= wdata;
                    ADDR_CHECKER_SZ: checker_sz <= wdata[2:0];
                    ADDR_PIX_CTRL:   begin invert <= wdata[0]; rb_swap <= wdata[1]; end
                    default: ;       // RO / unmapped: ignored
                endcase
            end
        end
    end

    // ---------------- read (combinational) ----------------
    always @(*) begin
        if      (base == ADDR_CHIP_ID)  rdata = hi_lane ? CHIP_ID_VAL[15:8] : CHIP_ID_VAL[7:0];
        else if (base == ADDR_H_ACTIVE) rdata = hi_lane ? {5'b0, h_active[10:8]} : h_active[7:0];
        else if (base == ADDR_V_ACTIVE) rdata = hi_lane ? {5'b0, v_active[10:8]} : v_active[7:0];
        else if (base == ADDR_SCRATCH)  rdata = hi_lane ? scratch[15:8] : scratch[7:0];
        else case (addr)
            ADDR_REV_ID:     rdata = REV_ID_VAL;
            ADDR_STATUS:     rdata = {7'b0, disp_active};
            ADDR_DISP_CTRL:  rdata = {6'b0, disp_ctrl};
            ADDR_TPG_MODE:   rdata = {5'b0, pattern};
            ADDR_FG_R:       rdata = fg_r;
            ADDR_FG_G:       rdata = fg_g;
            ADDR_FG_B:       rdata = fg_b;
            ADDR_CHECKER_SZ: rdata = {5'b0, checker_sz};
            ADDR_PIX_CTRL:   rdata = {6'b0, rb_swap, invert};
            default:         rdata = 8'h00;
        endcase
    end
endmodule
