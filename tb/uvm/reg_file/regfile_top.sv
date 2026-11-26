`timescale 1ns/1ps

module regfile_top
    import uvm_pkg::*;
    import regfile_test_pkg::regfile_smoke_test;
();
    logic clk = 0;

    localparam int CLK_PERIOD_NS = 10;

    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD_NS / 2) clk = ~clk;
    end

    regfile_if vif (clk);
    reg_file dut (
        .clk(clk),
        .reset(vif.reset),
        .rf_write_W(vif.we),
        .rs1_idx_rf(vif.rs1),
        .rs2_idx_rf(vif.rs2),
        .rd_idx_W(vif.rd),
        .WB_mux_result(vif.wdata),
        .rs1_val_D(vif.rs1_val),
        .rs2_val_D(vif.rs2_val)
    );

    `ifdef TRACE_VCD
        // The runner supplies an absolute path only when TRACE=1.
        initial begin : waveform_dump
            string trace_file;
            if ($value$plusargs("trace=%s", trace_file)) begin
                $dumpfile(trace_file);
                $dumpvars(0, regfile_top);
            end
        end
    `endif

    initial begin
        uvm_config_db#(virtual regfile_if)::set(null, "*", "vif", vif);
        run_test(regfile_smoke_test::type_name());
    end

endmodule
