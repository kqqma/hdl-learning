module baud_gen #(
    parameter int clk_freq = 50_000_000,
    parameter int baud = 115_200,
    parameter int oversample = 1
) (
    input logic clk,
    input logic resetn,
    input logic clear, 
    output logic tick
);

localparam int div = (clk_freq + (baud * oversample)/2) / (baud * oversample);
//calculate the number of clock cycles per tick

localparam int CW = $clog2(div);                   // counter width (9 for TX)
localparam logic [CW-1:0] LAST = CW'(div - 1);     // 433, but as a 9-bit value

logic [CW-1:0] count;
    
    always_ff @(posedge clk or negedge resetn) begin
        if (!resetn) 
            count <= 0;
        else if (count == LAST || clear)
            count <= '0;
        else
            count <= count + 1'b1;
    end
assign tick = (count == LAST);
endmodule
