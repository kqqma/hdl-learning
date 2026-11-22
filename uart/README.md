# UART (8N1) in SystemVerilog

Parameterized UART transmitter and receiver, verified using cocotb on all 256 byte values, bad stop bit, line glitches, and baud mismatch.

## Features

- 8N1 frames (1 start bit, 8 data bits LSB first, no parity, 1 stop bit), line idles high
- Parameterized clock frequency and baud rate (`clk_freq`, `baud`)
- TX: one-cycle `tx_start` pulse, `tx_busy` status
- RX: 2-FF synchronizer, 16× oversampling, start-bit validation (glitch rejection), `frame_err` on a bad stop bit
- Self-checking cocotb testbenches, including a TX → RX loopback

## Repository layout

```
uart/
├── rtl/
│   ├── baud_gen.sv        # tick generator (rounding divider, synchronous clear)
│   ├── uart_tx.sv
│   ├── uart_rx.sv
│   └── uart_loopback.sv   # TX wired to RX, for the end-to-end test
├── tb/
│   ├── Makefile
│   ├── test_baud_gen.py
│   ├── test_uart_tx.py
│   ├── test_uart_rx.py
│   └── test_uart_loopback.py
└── synth/
    ├── uart_tx_stat.txt
    └── uart_rx_stat.txt
```

## Design

### Frame format

   idle | start | b0 b1 b2 b3 b4 b5 b6 b7 | stop | idle
    1   |   0   |  1  0  0  0  0  0  1  0 |  1   |  1


### Baud generation

| | Formula | 50 MHz / 115200 | Actual rate | Error |
|---|---|---|---|---|
| TX tick (1 per bit) | `round(clk_freq / baud)` | 434 cycles | 115,207 baud | 0.006% |
| RX tick (16 per bit) | `round(clk_freq / (16 × baud))` | 27 cycles | 115,741 baud | 0.47% |


Separate clock dividers were chosen since the extra error from having both TX and RX on a single clock was more important than having a few extra ffs for another 5 bit counter for RX.
Rounding was used instead of truncating to ensure as little error as possible for the baudrate, although it was not especially necessary here, since 434.03 and 27.13 for TX and RX respectively both truncated to the closest value anyways.

### Transmitter (`uart_tx`)

- IDLE --tx_start--> START --tick--> DATA (8 ticks) --tick on bit 7--> STOP --tick--> IDLE

- Every 434 clock cycles, shift the shift register right, and give tx = shiftreg[0] in DATA. 
- baud_gen is cleared when a frame starts, so the start bit is always exactly one bit long.
- baud_clear is combinational and enabled when state is IDLE and tx_start is high, so baud_gen restarts on the same edge tx enters start.


### Receiver (`uart_rx`)

- IDLE -- RX falling edge --> START --8 ticks, RX still low --> DATA (16 ticks per, 8 bits) --> STOP --16 ticks--> IDLE
- baud_clear is enabled when state is IDLE and it occurs on a falling edge (accounting for bad stop bits)
- A 2-FF synchronizer was used for rx to avoid a metastable output. rx -> rx_meta -> rx_sync, which was then used for the rest of the code. 
- RX only allowed start bits on a falling edge of rx_sync, instead of just reading if line was low.
- frame_err pulses and rx_valid does not if stop bit is 0.

### Timing margin

because RX samples each bit in the middle, it can be off by around half a bit (216 clock cycles) at the stop-bit sample point (which is 9.5 bits after the start edge)
with a 2% sender error, which is 11  / 7 cycles per bit, results in 104 / 66 cycles of drift, which is well within the margin of error mentioned above. 

## Verification

All tests are self-checking cocotb tests running on Icarus Verilog. RTL is Verilator `-Wall` lint clean.

| Module | Test | What it checks | Result |
|---|---|---|---|
| `baud_gen` | `tick_period` | tick spacing is exactly DIV (`OVERSAMPLE` = 1 and 16) | ✅ |
| `baud_gen` | `clear_restarts_count` | after `clear`, the next tick is exactly DIV cycles later | ✅ |
| `uart_tx` | `send_bytes` | `0x41` decoded correctly by a Python bit-level receiver | ✅ |
| `uart_tx` | `send_random_bytes` | all 256 bytes, random `tx_start` timing vs. the baud tick | ✅ 256/256 |
| `uart_rx` | `receive_bytes` | `0x41` driven by a Python bit-level transmitter | ✅ |
| `uart_rx` | `receive_random_bytes` | all 256 bytes, random idle gaps, exactly 256 `rx_valid` and 0 `frame_err` | ✅ 256/256 |
| `uart_rx` | `bad_stop_bit` | `frame_err` pulses, no `rx_valid`, next good frame received | ✅ |
| `uart_rx` | `glitch_rejected_rx_low` | 50-cycle low glitch produces no byte and no error, next frame received | ✅ |
| `uart_rx` | `baud_mismatch_test` | all 256 bytes at +2% and −2% baud, alternating | ✅ 512/512 |
| `uart_loopback` | `send_and_receive_random_bytes` | `uart_tx` → `uart_rx`, all 256 bytes, random gaps | ✅ 256/256 |

for the cocotb tests, python acted as the receiver for TX and the sender for RX. this meant each design had been tested against an independent model, before against each other in the loopback tests

count_pulses ran for the entire test to ensure that every valid and frame error pulse was caught. This was added to ensure that extra valids or frame errors are found even though every expected byte was fine.

with_timeout() was used so that even if the hardware never responds (missing tx_start or fsm is stuck), the tests fails after two frame lengths.

## Bugs found during design and verification

### 1. RX reported a phantom 0xFF after a bad stop bit

after a bad stop bit, RX flagged frame_err at the middle of the stop bit and the state went to IDLE. Because RX was now in idle, and the line was still low, it read that low signal as a new start bit, and then filled in the next 8 data bits with 0xFF, which was the IDLE line staying high. since the stop bit was high as well, it counted as a valid frame and was sent. This was fixed by starting a frame only on a falling edge of rx_sync, not just when the line is low.

## Synthesis

predicted TX: counter - 9 bits, shiftreg - 8 bits, bitcounter - 3 bits, state register logic - 2 bits = 22
predicted RX: counter - 5 bits, shiftreg - 8 bits, bitcounter - 3 bits, tickcounter - 4 bits, 3 synchronizer ffs - 3 bits, rx data - 8 bits, valid and error registers - 2 bits, state register logic - 2 bits = 35


Yosys generic synthesis (`synth`), each module including its `baud_gen`:

| Module | Flip-flops | Logic cells | Total cells |
|---|---|---|---|
| `uart_tx` | 22 | 86 | 108 |
| `uart_rx` | 37 | 136 | 173 |

results: TX followed the predicted 22 ffs. RX differed by 2. this is because RX had an extra $_DFF_PN1 high reset ff. because IDLE is idle high, then the state register was one-hot encoded instead of binary by yosys. This added 2 bits since onehot resulted in 4 flops from 2 binary ones.

## How to run

```bash
# from the repo root, with the Python venv active
source .venv/bin/activate
cd uart/tb

make clean && make                             # baud_gen (OVERSAMPLE = 1)
make clean && make OVERSAMPLE=16               # baud_gen (OVERSAMPLE = 16)
make clean && make COCOTB_TOPLEVEL=uart_tx
make clean && make COCOTB_TOPLEVEL=uart_rx
make clean && make COCOTB_TOPLEVEL=uart_loopback
```

```bash
# lint (from the repo root)
verilator --lint-only -Wall --top-module uart_loopback \
    uart/rtl/uart_loopback.sv uart/rtl/uart_tx.sv uart/rtl/uart_rx.sv uart/rtl/baud_gen.sv

# synthesis stats
yosys -p "read_verilog -sv uart/rtl/baud_gen.sv uart/rtl/uart_tx.sv; synth -top uart_tx; stat"
yosys -p "read_verilog -sv uart/rtl/baud_gen.sv uart/rtl/uart_rx.sv; synth -top uart_rx; stat"
```

Tools: Icarus Verilog 12.0, cocotb 2.1, Verilator 5.032, Yosys.

## What I learned

- RX can't use rx directly - since if it samples on the exact moment it switches, then it could sample a metastable value. this was fixed by having a 2-FF synchronizer where rx -> rx_meta -> rx_sync, which was then used instead to guarantee sampling a stable value.

- Originally, RX started a frame whenever state was IDLE and the line was low. This was an issue since if there was a bad stop bit, then the line was still low, and RX received a false 0xFF frame. This was fixed by having START only occur after a falling edge.

- In cocotb, for the RX test, rx_valid is a one cycle pulse at the middle of the stop bit if stop is high, but send_byte only returns at the end of the stop bit. In the situation where send_byte is called and waits for rx_valid (which already pulsed half a bit earlier), in the test, wait_for_byte will await for rx_valid forever and the test will timeout. This was fixed by starting the listener (wait_for_byte) before sending.

## Next steps
- run the echo demo on an FPGA board.
- submit uart_tx to Tiny Tapeout.
- optional parity bit, majority-vote sampling in RX.