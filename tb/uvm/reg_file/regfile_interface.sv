interface regfile_if(input logic clk);
    logic reset;
    logic we;
    logic [4:0] rd;
    logic [31:0] wdata;
    logic [4:0] rs1;
    logic [4:0] rs2;
    logic [31:0] rs1_val;
    logic [31:0] rs2_val;
endinterface //regfile_if(input logic clk)logic 
