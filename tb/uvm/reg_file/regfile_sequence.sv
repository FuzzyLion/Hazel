`include "uvm_macros.svh"

package regfile_sequence_pkg;
    import uvm_pkg::*;
    import regfile_pkg::regfile_item;

    class regfile_smoke_sequence extends uvm_sequence #(regfile_item);
        `uvm_object_utils(regfile_smoke_sequence)

        function new(string name = "regfile_smoke_sequence");
            super.new(name);
        endfunction //new()

        virtual task automatic body();
            req = regfile_item::type_id::create("write_x7");
            start_item(req);
            req.reset = 1'b0;
            req.we = 1'b1;
            req.rd = 5'd7;
            req.wdata = 32'd20;
            req.rs1 = 5'd0;
            req.rs2 = 5'd0;
            finish_item(req);

            req = regfile_item::type_id::create("read_x7");
            start_item(req);
            req.reset = 1'b0;
            req.we = 1'b0;
            req.rd = 5'd0;
            req.wdata = 32'd0;
            req.rs1 = 5'd7;
            req.rs2 = 5'd0;
            finish_item(req);
        endtask //automatic

    endclass
endpackage : regfile_sequence_pkg
