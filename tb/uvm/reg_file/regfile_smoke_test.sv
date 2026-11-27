`include "uvm_macros.svh"

package regfile_test_pkg;
    import uvm_pkg::*;
    import regfile_pkg::regfile_item;
    import regfile_sequence_pkg::regfile_smoke_sequence;
    import regfile_driver_pkg::regfile_driver;
    import regfile_monitor_pkg::regfile_monitor;

    class regfile_smoke_test extends uvm_test;
        `uvm_component_utils(regfile_smoke_test)

        uvm_sequencer #(regfile_item) sqr;
        regfile_driver drv;
        regfile_monitor mon;

        function new(string name = "regfile_smoke_test", uvm_component parent = null);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            sqr = uvm_sequencer #(regfile_item)::type_id::create("sqr", this);
            drv = regfile_driver::type_id::create("drv", this);
            mon = regfile_monitor::type_id::create("mon", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            drv.seq_item_port.connect(sqr.seq_item_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            regfile_smoke_sequence seq = regfile_smoke_sequence::type_id::create("seq");

            phase.raise_objection(this);
            seq.start(sqr);
            #2ns;  // Allow the monitor to finish its final sample
            phase.drop_objection(this);
        endtask
    endclass
endpackage : regfile_test_pkg
