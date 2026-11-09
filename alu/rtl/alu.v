module alu #(parameter WIDTH = 4) (
    input  [WIDTH-1:0] a, b,
    input  [2:0]       op,
    output reg [WIDTH-1:0] y,
    output reg         z, n, c, v
);
    always @(*) begin
        //defaults
        y = 0;
        {c, v} = 2'b00;

        case (op)
        3'b000 : begin
            {c,y} = a + b; // add with carry
            v = (a[WIDTH-1] ~^ b[WIDTH-1]) & (a[WIDTH-1] ^ y[WIDTH-1]);
            end
        3'b001 : begin
            {c,y} = a - b; // sub
            v = (a[WIDTH-1] ^ b[WIDTH-1]) & (a[WIDTH-1] ^ y[WIDTH-1]);
            end
        3'b010 : y = a & b; // and
        3'b011 : y = a | b; // or
        3'b100 : y = a ^ b; // xor
        3'b101 : y = ~a;    // not
        3'b110 : y = a << 1; // shift left
        3'b111 : y = ($signed(a) < $signed(b)) ? 1 : 0; // less than
        default: y = 0; // default case
        endcase
        z = ~(|y);
        n = (y[WIDTH-1]);
    end
endmodule
