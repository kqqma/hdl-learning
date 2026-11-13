`timescale 1ns/1ps
module fsmmealy(
    input clk,
    input in,
    input reset,
    output out); //
    localparam A = 0, B = 1, C = 2, D = 3;
    reg [1:0] state, next_state;
    always @(*) begin
    case (state)
        A: next_state = (in) ? B : A;
        B: next_state = (in) ? B : C;
        C: next_state = (in) ? D : A;
        D: next_state = (in) ? B : C;

        default: next_state = A;
    endcase
    end
    
    always @(posedge clk) begin 
        if (reset) 
            state <= A;
		else
            state <= next_state;
    end
    // Output logic:  out = f(state) for a Moore state machine
    assign out = ((state == D) && (in == 1));

    // Output logic

endmodule
