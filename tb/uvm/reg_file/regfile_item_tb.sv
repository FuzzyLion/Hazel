`timescale 1ns/1ps

module regfile_item_tb;

    import regfile_pkg::*;

    regfile_item item;
    initial begin
        int round;
        item = regfile_item::type_id::create("item");

        for (round = 0; round < 5; round++) begin
            if (item.randomize() == 1) begin
                item.print();
            end
            else begin
                $fatal(1, "Random stimulus generated failure");
            end
            
        end
        $finish;
    end

endmodule
