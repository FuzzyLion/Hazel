`include "uvm_macros.svh"

package regfile_monitor_pkg;
    import uvm_pkg::*;
    import regfile_pkg::regfile_item;

    class regfile_monitor extends uvm_monitor;
        `uvm_component_utils(regfile_monitor)

        virtual regfile_if vif;
        uvm_analysis_port #(regfile_item) ap;

        function new(string name = "regfile_monitor", uvm_component parent);
            super.new(name, parent);
        endfunction //new()

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            ap = new("ap", this);

            if (!uvm_config_db#(virtual regfile_if)::get(this, "", "vif", vif)) begin
                // Bind this virtual interface handle to the shared physical interface in tb_top
                `uvm_fatal("NOVIF", "regfile_monitor could not get vif from uvm_config_db")
            end
        endfunction

        virtual task automatic run_phase(uvm_phase phase);
            regfile_item item;

            forever begin
                item = regfile_item::type_id::create("item");

                @(posedge vif.clk);
                #1ns;

                // Use blocking assignments so all sampled fields are updated before ap.write(item)
                item.reset = vif.reset;
                item.we = vif.we;
                item.rd = vif.rd;
                item.wdata = vif.wdata;
                item.rs1 = vif.rs1;
                item.rs2 = vif.rs2;
                item.rs1_val = vif.rs1_val;
                item.rs2_val = vif.rs2_val;

                item.print();
                ap.write(item);
            end
        endtask //automatic

    endclass //regfile_monitor
endpackage : regfile_monitor_pkg
