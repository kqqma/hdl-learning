module uart_loopback #(
    parameter int clk_freq = 50_000_000,
    parameter int baud = 115_200
)(
    input logic clk,
    input logic resetn,
    input logic tx_start,
    input logic [7:0] tx_data,

    output logic [7:0] rx_data,
    output logic rx_valid,
    output logic frame_err,
    output logic tx_busy
);

logic serial;
uart_tx #(.clk_freq(clk_freq), .baud(baud)) u_tx(.clk(clk), .resetn(resetn), .tx_start(tx_start), .tx_data(tx_data), .tx(serial), .tx_busy(tx_busy));
uart_rx #(.clk_freq(clk_freq), .baud(baud)) u_rx(.clk(clk), .resetn(resetn), .rx(serial), .rx_data(rx_data), .rx_valid(rx_valid), .frame_err(frame_err));

endmodule
