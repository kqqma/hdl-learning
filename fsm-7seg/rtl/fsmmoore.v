`timescale 1ns/1ps
module fsmmoore(
    input clk,
    input in,
    input reset,
    output out); //
    localparam A = 0, B = 1, C = 2, D = 3, E=4;
    reg [2:0] state, next_state;
    always @(*) begin
    case (state)
        A: next_state = (in) ? B : A;
        B: next_state = (in) ? B : C;
        C: next_state = (in) ? D : A;
        D: next_state = (in) ? E : C;
        E: next_state = (in) ? B : C;
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
    assign out = (state == E);

    // Output logic

endmodule
