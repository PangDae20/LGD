// I2C master tasks (7-bit address, open-drain SDA via m_sda_low, SCL push-pull)
// included inside tb_harness. Uses: scl, sda, m_sda_low, dev, Q
    task i2c_start; begin m_sda_low = 0; scl = 1; #Q m_sda_low = 1; #Q scl = 0; #Q; end endtask
    task i2c_rstart; begin m_sda_low = 0; #Q scl = 1; #Q m_sda_low = 1; #Q scl = 0; #Q; end endtask
    task i2c_stop; begin m_sda_low = 1; #Q scl = 1; #Q m_sda_low = 0; #(2*Q); end endtask
    task i2c_wbyte(input [7:0] bv, output ack_n);
        integer k;
        begin
            for (k = 7; k >= 0; k = k - 1) begin
                m_sda_low = ~bv[k]; #Q scl = 1; #(2*Q) scl = 0; #Q;
            end
            m_sda_low = 0; #Q scl = 1; #Q ack_n = sda; #Q scl = 0; #Q;
        end
    endtask
    task i2c_rbyte(input send_nack, output [7:0] bv);
        integer k;
        begin
            m_sda_low = 0; bv = 0;
            for (k = 7; k >= 0; k = k - 1) begin
                #Q scl = 1; #Q bv = {bv[6:0], sda}; #Q scl = 0; #Q;
            end
            m_sda_low = ~send_nack; #Q scl = 1; #(2*Q) scl = 0; #Q m_sda_low = 0;
        end
    endtask
    task i2c_write(input [6:0] ad, input [7:0] wd, output err);
        reg n1, n2, n3;
        begin
            i2c_start; i2c_wbyte({dev, 1'b0}, n1); i2c_wbyte({1'b0, ad}, n2); i2c_wbyte(wd, n3); i2c_stop;
            err = n1 | n2 | n3;
        end
    endtask
    task i2c_read(input [6:0] ad, output [7:0] rv, output err);
        reg n1, n2, n3;
        begin
            i2c_start; i2c_wbyte({dev, 1'b0}, n1); i2c_wbyte({1'b0, ad}, n2);
            i2c_rstart; i2c_wbyte({dev, 1'b1}, n3); i2c_rbyte(1'b1, rv); i2c_stop;
            err = n1 | n2 | n3;
        end
    endtask

