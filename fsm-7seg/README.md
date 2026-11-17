# Sequence Detector FSM + 7-Segment Decoder

Two small RTL designs written in Verilog-2005, simulated with Icarus Verilog, linted with Verilator and synthesized with Yosys:

1. **1011 sequence detector**: detects the pattern `1011` in a serial bit stream (overlapping matches allowed), built as both a **Moore** and a **Mealy** FSM
2. **Hex-to-7-segment decoder**: maps a 4-bit value (0–F) to the 7 segments of a display

## Directory layout

```
fsm-7seg/
├── rtl/
│   ├── fsmmoore.v      # Moore 1011 detector (5 states)
│   ├── fsmmealy.v      # Mealy 1011 detector (4 states)
│   └── sevenseg.v      # hex-to-7-segment decoder
└── tb/
    ├── fsmtb.v         # self-checking testbench for both FSMs
    └── tb_sevenseg.v   # exhaustive testbench for the decoder
```

## 1011 sequence detector

### Moore state table

| State | Meaning | in = 0 | in = 1 | out |
|---|---|---|---|---|
| A | nothing matched | A | B | 0 |
| B | matched `1` | C | B | 0 |
| C | matched `10` | A | D | 0 |
| D | matched `101` | C | E | 0 |
| E | matched `1011` | C | B | 1 |

### Mealy state table

| State | Meaning | in = 0 | in = 1 | out |
|---|---|---|---|---|
| A | nothing matched | A | B | 0 |
| B | matched `1` | C | B | 0 |
| C | matched `10` | A | D | 0 |
| D | matched `101` | C | B | 1 |


### Moore vs. Mealy timing

Mealy machine goes high one cycle before Moore since Mealy can read the current input and know that 1011 has been detected before the clock cycle has passed

## Hex-to-7-segment decoder

- **Output:** `seg[6:0] = {g,f,e,d,c,b,a}`, active-high (1 = segment on)
- Letters shown as A, b, C, d, E, F
- 9 is drawn without segment d

```
   aaa
  f   b
   ggg
  e   c
   ddd
```

## How to run

Requires Icarus Verilog, Verilator, Yosys, Cocotb.

```bash
# FSM testbench
iverilog -Wall -o sim rtl/fsmmoore.v rtl/fsmmealy.v tb/fsmtb.v && vvp sim

# 7-segment testbench
iverilog -Wall -o sim7 rtl/sevenseg.v tb/tb_sevenseg.v && vvp sim7

# Lint
verilator --lint-only -Wall rtl/fsmmoore.v
verilator --lint-only -Wall rtl/fsmmealy.v
verilator --lint-only -Wall rtl/sevenseg.v

# Synthesis stats (add -nofsm after the -top name to keep binary state encoding)
yosys -p "read_verilog rtl/fsmmoore.v; synth -top fsmmoore; stat"

# Waveforms
gtkwave fsmtb.vcd

#Cocotb
make //for 7 seg decoder
make COCOTB_TOPLEVEL=fsmmoore
make COCOTB_TOPLEVEL=fsmmealy
```

## Verification

- **FSMs:** the same bit stream drives both machines, and each output is checked mid-cycle against hand-traced expected values, which also checks the one-cycle Moore/Mealy offset.

- **Decoder:** all 16 inputs are checked against a truth table written separately from the RTL.

## Results

| Design | Encoding | Flip-flops | Total cells |
|---|---|---|---|
| Moore 1011 detector | one-hot (Yosys default) | 5 | 18 |
| Moore 1011 detector | binary (`-nofsm`) | 3 | 29 |
| Mealy 1011 detector | one-hot (Yosys default) | 4 | 16 |
| Mealy 1011 detector | binary (`-nofsm`) | 2 | 14 |
| Hex-to-7-seg decoder | n/a (combinational) | 0 | 32 (15 are 2:1 muxes) |



- All testbenches pass
- Verilator `-Wall` lint clean

Used cocotb on Icarus as a test bench, with one Makefile paramaterized by the top module. For decoder: exhaustive over all 16 inputs. For FSMs: sliding window was used, with a directed 1011011 sequence to check for overlap, and 1000 random bits with a logged match count.

Moore vs Mealy timing.
- for the cocotb testbenches, moore was checked after the rising edge, and mealy was checked within the same cycle, before the edge. The way this difference was achieved was by moving where the output lines were between the rising/falling edge and awaiting timers.

### Observations

When running Yosys, for the Moore detector binary was 29 and one-hot (yosys default) was 18 cells. With one-hot, checking “am I in state D?” is just one flip-flop’s output. With binary, 5 states need 3 bits, so every state check compares 3 bits against a code, and 3 of the 8 codes are never used. That extra decode logic outweighed the 2 flip-flops binary saves (3 vs. 5). This was flipped for the Mealy detector, where binary was 14 and one-hot was 16 total cells. 4 states use exactly the 4 codes of 2 bits, so no codes go unused and the decode logic stays small. Binary also uses 2 fewer flip-flops (2 vs. 4).Running again for the seven segment resulted in 32 total cells, mostly MUXes.



## Lessons learned
Including #1 in the test bench.
 - Because the simulator doesnt execute every block of code parallel, if the testbench checks the out variable without the #1 time unit delay, it would see a previous digit pattern and assume an error. With the #1 time delay, the testbench sits for a unit, and allows the decoders always block to run, meaning variable out updates, and then the testbench will continue and check. Note: that is not a gate delay, and only the order in which the simulator runs.

- after driving an input, cocotb needs an await Timer(1, unit="ns") line before reading the output to allow for it to settle.

- calling reset_fsm(dut) without the await at the start meant the reset never ran, even though the cocotb tests say it passed, since the RTL's default case happened to recover. this was discovered by reading through cocotb's warnings