`timescale 1ns/1ps
module counter_tb;
    reg clk = 0;
    reg reset = 1;
    wire [3:0] q;

    counter dut (.clk(clk), .reset(reset), .q(q));  // "dut" = device under test

    always #5 clk = ~clk;   // flip the clock every 5 ns -> 10 ns period

    initial begin
        $dumpfile("counter.vcd");   // file to save the waveform in
        $dumpvars(0, counter_tb);   // record every signal in the testbench
        #12 reset = 0;              // release reset after 12 ns
        #200 $finish;               // run 200 more ns, then stop
    end
endmodule
