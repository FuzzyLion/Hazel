`timescale 1ns/1ps
`include "uvm_macros.svh"

package regfile_driver_pkg;
    import uvm_pkg::*;
    import regfile_pkg::regfile_item;

    class regfile_driver extends uvm_driver #(regfile_item);
        `uvm_component_utils(regfile_driver)
        virtual regfile_if vif;

        function new(string name = "regfile_driver", uvm_component parent);
            super.new(name, parent);
        endfunction //new()

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual regfile_if)::get(this, "", "vif", vif)) begin
                `uvm_fatal("NOVIF", "regfile_driver could not get vif from uvm_config_db")
            end
        endfunction

        virtual task automatic run_phase(uvm_phase phase);
            forever begin
                seq_item_port.get_next_item(req);

                @(negedge vif.clk);
                vif.reset <= req.reset;
                vif.we <= req.we;
                vif.rd <= req.rd;
                vif.wdata <= req.wdata;
                vif.rs1 <= req.rs1;
                vif.rs2 <= req.rs2;

                @(posedge vif.clk);

                seq_item_port.item_done();
            end
        endtask //automatic

    endclass
endpackage : regfile_driver_pkg
