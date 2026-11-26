package regfile_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    class regfile_item extends uvm_sequence_item;

        rand bit we, reset;
        rand logic [4:0] rd, rs1, rs2;
        rand logic [31:0] wdata;

        // UVM uses wide packer and comparer arguments for every field.
        /* verilator lint_off WIDTHEXPAND */
        /* verilator lint_off WIDTHTRUNC */
        `uvm_object_utils_begin(regfile_item)
            `uvm_field_int(reset, UVM_DEFAULT)
            `uvm_field_int(we, UVM_DEFAULT)
            `uvm_field_int(rd, UVM_DEFAULT)
            `uvm_field_int(wdata, UVM_DEFAULT)
            `uvm_field_int(rs1, UVM_DEFAULT)
            `uvm_field_int(rs2, UVM_DEFAULT)
        `uvm_object_utils_end
        /* verilator lint_on WIDTHTRUNC */
        /* verilator lint_on WIDTHEXPAND */

        function new(string name = "regfile_item");
            super.new(name);
        endfunction //new()
    endclass //regfile_item extends uvm_sequence_item
endpackage : regfile_pkg
