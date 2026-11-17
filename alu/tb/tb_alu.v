`timescale 1ns/1ps

module tb_alu;
    // signals you drive -> reg; signals the DUT drives -> wire
    reg  [3:0] a, b;
    reg  [2:0] op;
    wire [3:0] y;
    wire       z, n, c, v;

    integer errors = 0;

    // instantiate the DUT with named ports
    alu #(.WIDTH(4)) dut (.a(a), .b(b), .op(op), .y(y), .z(z), .n(n), .c(c), .v(v));

    // self-checking helper: apply inputs, wait, compare against expected values
    task check(input [2:0] t_op, input [3:0] t_a, t_b,
               input [3:0] exp_y, input exp_z, exp_n, exp_c, exp_v);
        begin
            op = t_op; a = t_a; b = t_b;
            #10;  // let the combinational logic settle
            if ({y, z, n, c, v} !== {exp_y, exp_z, exp_n, exp_c, exp_v}) begin
                $display("FAIL op=%b a=%b b=%b | got y=%b zncv=%b%b%b%b | expected y=%b zncv=%b%b%b%b",
                t_op, t_a, t_b, y, z, n, c, v, exp_y, exp_z, exp_n, exp_c, exp_v);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("alu.vcd");     // waveform file for GTKWave
        $dumpvars(0, tb_alu);

        //add
        check(3'b000, 4'b0010, 4'b0011,   4'b0101, 0, 0, 0, 0); // 2 + 3 = 5, no flags
        check(3'b000, 4'b1111, 4'b0001,   4'b0000, 1, 0, 1, 0); // carry out, result 0 (-1 + 1 = 0 signed, so no V)
        check(3'b000, 4'b0111, 4'b0001,   4'b1000, 0, 1, 0, 1); // pos + pos overflow (7 + 1)
        check(3'b000, 4'b1000, 4'b1000,   4'b0000, 1, 0, 1, 1); // neg + neg overflow (-8 + -8)

        // logic op right after C=1/V=1: catches missing defaults
        check(3'b010, 4'b1100, 4'b0011,   4'b0000, 1, 0, 0, 0); // AND, no common bits -> Z

        //sub
        check(3'b001, 4'b0101, 4'b0011,   4'b0010, 0, 0, 0, 0); // 5 - 3 = 2, no borrow
        check(3'b001, 4'b0011, 4'b0101,   4'b1110, 0, 1, 1, 0); // 3 - 5: borrow, result -2
        check(3'b001, 4'b1000, 4'b0001,   4'b0111, 0, 0, 0, 1); // -8 - 1: signed overflow, wraps to +7
        check(3'b001, 4'b0100, 4'b0100,   4'b0000, 1, 0, 0, 0); // equal inputs -> Z

        //logical ops
        check(3'b010, 4'b1100, 4'b1010,   4'b1000, 0, 1, 0, 0); // AND, top bit set -> N
        check(3'b011, 4'b1100, 4'b0011,   4'b1111, 0, 1, 0, 0); // OR -> all ones
        check(3'b100, 4'b1010, 4'b1010,   4'b0000, 1, 0, 0, 0); // XOR x^x = 0 -> Z
        check(3'b101, 4'b0000, 4'b1010,   4'b1111, 0, 1, 0, 0); // NOT 0 = 1111, b ignored

        //shl
        check(3'b110, 4'b1001, 4'b0000,   4'b0010, 0, 0, 0, 0); // top bit falls off, C stays 0

        //slt
        check(3'b111, 4'b0010, 4'b0101,   4'b0001, 0, 0, 0, 0); // 2 < 5
        check(3'b111, 4'b1111, 4'b0001,   4'b0001, 0, 0, 0, 0); // -1 < 1 (fails without $signed)
        check(3'b111, 4'b0001, 4'b1111,   4'b0000, 1, 0, 0, 0); // 1 < -1 is false (unsigned would say true)
        check(3'b111, 4'b0011, 4'b0011,   4'b0000, 1, 0, 0, 0); // equal -> 0 (catches <= bug)

        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("%0d TEST(S) FAILED", errors);
        $finish;
    end
endmodule