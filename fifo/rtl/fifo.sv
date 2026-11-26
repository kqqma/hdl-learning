module fifo #(
    parameter int DEPTH = 4,
    parameter int WIDTH = 8
)(
    input logic clk,
    input logic reset,
    input logic wr_en,
    input logic [WIDTH-1:0] wr_data, 
    input logic rd_en,

    output logic [WIDTH-1:0] rd_data,
    output logic full, 
    output logic empty
);

localparam int AW = $clog2(DEPTH);
logic [WIDTH-1:0] mem [DEPTH];
logic [AW:0] wr_ptr;
logic [AW:0] rd_ptr; 
logic push, pop;

assign pop  = rd_en && (!empty);
assign push = wr_en && (!full || pop);

assign full = (wr_ptr[AW-1:0] == rd_ptr[AW-1:0] && wr_ptr[AW] != rd_ptr[AW]);
assign empty = (wr_ptr == rd_ptr);



always_ff @(posedge clk) begin

    if (reset) begin
    wr_ptr <= 0;
    rd_ptr <= 0;
    end
    else begin
    if (push) begin
        wr_ptr <= wr_ptr + 1;
    mem[wr_ptr[AW-1:0]] <= wr_data;
    end
    end 
    if (pop) begin
        rd_ptr <= rd_ptr + 1;
    rd_data <= mem[rd_ptr[AW-1:0]];
    end
end

endmodule
