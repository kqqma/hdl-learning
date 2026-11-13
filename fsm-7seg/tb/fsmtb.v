`timescale 1ns/1ps
module fsmtb;
  reg clk = 0, reset = 1, in = 0;
  wire out_moore, out_mealy;

  fsmmoore u_moore (.clk(clk), .reset(reset), .in(in), .out(out_moore));
  fsmmealy u_mealy (.clk(clk), .reset(reset), .in(in), .out(out_mealy));

  always #5 clk = ~clk;   // 10 ns period

  // cycle:              0 1 2 3 4 5 6 7
  reg [0:7] stream    = 8'b1_0_1_1_0_1_1_0;
  reg [0:7] exp_mealy = 8'b0_0_0_1_0_0_1_0;   // TODO
  reg [0:7] exp_moore = 8'b0_0_0_0_1_0_0_1;   // TODO

  integer i, errors = 0;
  initial begin
    $dumpfile("fsmtb.vcd"); $dumpvars(0, fsmtb);

    @(posedge clk); @(posedge clk); #1 reset = 0;

    for (i = 0; i < 8; i = i + 1) begin
      in = stream[i];          // drive 1 ns after the rising edge
      @(negedge clk);          // check mid-cycle, when everything has settled
      if (out_mealy !== exp_mealy[i]) begin
        $display("FAIL mealy cycle %0d: got %b exp %b", i, out_mealy, exp_mealy[i]);
        errors = errors + 1;
      end
            if (out_moore !== exp_moore[i]) begin
        $display("FAIL moore cycle %0d: got %b exp %b", i, out_moore, exp_moore[i]);
        errors = errors + 1;
      end

      @(posedge clk); #1;

    end

    if (errors == 0) $display("PASS");
    else             $display("%0d errors", errors);
    $finish;
  end
endmodule