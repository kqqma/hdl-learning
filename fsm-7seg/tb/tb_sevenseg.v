`timescale 1ns/1ps
module tb_sevenseg;
  reg  [3:0] in;
  wire [6:0] out;
  sevenseg dut (.in(in), .out(out));

  reg [6:0] expected [0:15];   // an array of 16 entries, each 7 bits
  integer i, errors = 0;

  initial begin
    // Fill from your hand-drawn truth table, not by copying the RTL
expected[0] = 7'b0111111;
expected[1] = 7'b0000110;
expected[2] = 7'b1011011;
expected[3] = 7'b1001111;
expected[4] = 7'b1100110;
expected[5] = 7'b1101101;
expected[6] = 7'b1111101;
expected[7] = 7'b0000111;
expected[8] = 7'b1111111;
expected[9] = 7'b1100111;
expected[10] = 7'b1110111;
expected[11] = 7'b1111100;
expected[12] = 7'b0111001;
expected[13] = 7'b1011110;
expected[14] = 7'b1111001;
expected[15] = 7'b1110001;
    // ... expected[1] through expected[15]

    for (i = 0; i < 16; i = i + 1) begin
      in = i;
      #1;   // why do you need a delay here?
      if (out !== expected[i]) begin
        $display("FAIL in=%h: got %b exp %b", i, out, expected[i]);
        errors = errors + 1;
      end
    end

    if (errors == 0) $display("PASS"); else $display("%0d errors", errors);
    $finish;
  end
endmodule