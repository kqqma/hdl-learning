module uart_rx #(
    parameter int clk_freq = 50_000_000,
    parameter int baud     = 115_200
)(
    input  logic       clk,
    input  logic       resetn,
    input  logic       rx,
    output logic [7:0] rx_data,
    output logic       rx_valid,
    output logic       frame_err
);

typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
state_t state;

logic baud_clear;
logic tick; //for baudgen

baud_gen #(.clk_freq(clk_freq), .baud(baud), .oversample(16)) u_baud (.clk(clk), .resetn(resetn), .clear(baud_clear), .tick(tick));

logic [7:0] shiftreg;
logic [2:0] bitcounter;
logic [3:0] tickcounter;
logic rx_meta, rx_sync;

assign baud_clear = (state == IDLE) && !rx_sync;

always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) begin
        rx_meta <= 1'b1;   // idle-high
        rx_sync <= 1'b1;
    end else begin
        rx_meta <= rx;       // might go metastable
        rx_sync <= rx_meta;  // has a full clock cycle to settle first
    end

end

always_ff @(posedge clk or negedge resetn) begin
    if (!resetn) begin
    state       <= IDLE;
    tickcounter <= '0;
    bitcounter  <= '0;
    shiftreg    <= '0;
    rx_data     <= '0;
    rx_valid    <= 1'b0;
    frame_err   <= 1'b0;
    end else begin
        rx_valid  <= 1'b0;   // default: no pulse
        frame_err <= 1'b0;

        case(state)

        IDLE: begin
        if (!rx_sync) begin
        state <= START;
        tickcounter <= '0;
        end
        end
        START: begin
        if (tick) begin
            if (tickcounter == 4'd7) begin      // this is the 8th tick
              tickcounter <= '0;
              if (rx_sync)
                  state <= IDLE;              // glitch
               else begin
                  bitcounter <= '0;
                  state <= DATA;
              end
            end else begin
                tickcounter <= tickcounter + 1'b1;
            end
        end
        end
        DATA: begin         
        if (tick) begin
            if (tickcounter == 4'd15) begin
            shiftreg <= {rx_sync, shiftreg[7:1]};
            tickcounter <= '0;
            if (bitcounter == 3'd7)
            state <= STOP;
                else begin
                  bitcounter <= bitcounter + 1'b1;
                end
            end else begin
                tickcounter <= tickcounter + 1'b1;
            end
        end
        end
        STOP: begin
        if (tick) begin
            if (tickcounter == 4'd15) begin
                if (rx_sync) begin
                rx_data <= shiftreg;
                rx_valid <= 1'b1;
                state <= IDLE;
                end else begin
                frame_err <= 1'b1;
                state <= IDLE;
                end
            end else begin 
            tickcounter <= tickcounter + 1'b1;
            end
        end
        end
        endcase
    end
    end
endmodule
