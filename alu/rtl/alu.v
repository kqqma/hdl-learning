module alu #(parameter WIDTH = 4) (
    input  [WIDTH-1:0] a, b,
    input  [2:0]       op,
    output reg [WIDTH-1:0] y,
    output reg         z, n, c, v
);
    always @(*) begin
        //defaults
        y = 4'b0000;
        {c, v} = 2'b00;

        case (op)
        3'b000 : begin
            {c,y} = a + b; // add with carry
            v = (a[3] ~^ b[3]) & (a[3] ^ y[3]);
            end
        3'b001 : begin
            y = a - b; // sub
            v = (a[3] ^ b[3]) & (a[3] ^ y[3]);
        3'b010 : y = a & b; // and
        3'b011 : y = a | b; // or
        3'b100 : y = a ^ b; // xor
        3'b101 : y = ~a;    // not
        3'b110 : y = a << 1; // shift left
        3'b111 : y = (a>b) ? 0 : 1; // less than
        default: y = 4'b0000; // default case
        endcase
    end
endmodule