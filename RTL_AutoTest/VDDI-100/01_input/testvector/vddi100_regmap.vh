// VDDI-100 register definitions — 설계/검증 공용 헤더 (사양서 4장 기준)
// 16-bit registers: big-endian byte order (사양서 기재)
// 형식: localparam ADDR_<이름> = <주소>; // REG width=.. access=.. reset=.. rw_mask=.. desc=".."
localparam [6:0] ADDR_CHIP_ID    = 7'h00; // REG width=16 access=RO reset=0xD1A5 rw_mask=0x0000 desc="Device ID"
localparam [6:0] ADDR_REV_ID     = 7'h02; // REG width=8  access=RO reset=0x10 rw_mask=0x00 desc="Silicon revision"
localparam [6:0] ADDR_STATUS     = 7'h03; // REG width=8  access=RO reset=0x00 rw_mask=0x00 desc="[0] DISP_ACTIVE" volatile=1
localparam [6:0] ADDR_H_ACTIVE   = 7'h04; // REG width=16 access=RW reset=0x0040 rw_mask=0x07FF desc="[10:0] H active pixels"
localparam [6:0] ADDR_V_ACTIVE   = 7'h06; // REG width=16 access=RW reset=0x0030 rw_mask=0x07FF desc="[10:0] V active lines"
localparam [6:0] ADDR_DISP_CTRL  = 7'h08; // REG width=8  access=RW reset=0x00 rw_mask=0x03 desc="[0] DISP_ON [1] TPG_EN"
localparam [6:0] ADDR_TPG_MODE   = 7'h09; // REG width=8  access=RW reset=0x01 rw_mask=0x07 desc="[2:0] PATTERN"
localparam [6:0] ADDR_FG_R       = 7'h0A; // REG width=8  access=RW reset=0xFF rw_mask=0xFF desc="Foreground R"
localparam [6:0] ADDR_FG_G       = 7'h0B; // REG width=8  access=RW reset=0xFF rw_mask=0xFF desc="Foreground G"
localparam [6:0] ADDR_FG_B       = 7'h0C; // REG width=8  access=RW reset=0xFF rw_mask=0xFF desc="Foreground B"
localparam [6:0] ADDR_CHECKER_SZ = 7'h0D; // REG width=8  access=RW reset=0x03 rw_mask=0x07 desc="[2:0] log2 cell size"
localparam [6:0] ADDR_PIX_CTRL   = 7'h0E; // REG width=8  access=RW reset=0x00 rw_mask=0x03 desc="[0] INVERT [1] RB_SWAP"
localparam [6:0] ADDR_SCRATCH    = 7'h10; // REG width=16 access=RW reset=0x0000 rw_mask=0xFFFF desc="Scratch"
localparam [6:0] I2C_DEV_ADDR     = 7'h3C; // I2C 7-bit device address
