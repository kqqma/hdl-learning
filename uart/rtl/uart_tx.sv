module uart_tx #(
    parameter int clk_freq = 50_000_000,
    parameter int baud     = 115_200
)(
    input logic clk,
    input logic resetn,
    input logic tx_start,
    input logic [7:0] tx_data,
    output logic tx,
    output logic tx_busy
);

typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
state_t state;

logic baud_clear;
logic tick; //for baudgen

baud_gen #(.clk_freq(clk_freq), .baud(baud), .oversample(1)) u_baud (.clk(clk), .resetn(resetn), .clear(baud_clear), .tick(tick));
assign baud_clear = (state == IDLE) && tx_start;
logic [7:0] shiftreg;
logic [2:0] bitcounter;

always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) begin
        state <= IDLE;
        shiftreg <= '0; //fill zeros
        bitcounter <= '0;
        end
    else begin 

        case (state)
            IDLE: begin
            if (tx_start) begin
                shiftreg <= tx_data;
                state <= START;
                end
            end
            START: begin
            if (tick) begin
                bitcounter <= '0;
                state <= DATA;
                end
            end
            DATA: begin
            if (tick) begin
                shiftreg <= shiftreg >> 1;
                if (bitcounter == 3'b111)
                    state <= STOP;
                else
                    bitcounter <= bitcounter + 1'b1;
                end
            end
            STOP: begin
            if (tick)
                state <= IDLE;
            end
        endcase
    end
    end

always_comb begin
    case(state)
        IDLE: tx = 1'b1;
        START: tx = 1'b0;
        DATA: tx = shiftreg[0];
        STOP: tx = 1'b1;
        default: tx = 1'b1;
    endcase
end
assign tx_busy = (state != IDLE);
endmodule


            

