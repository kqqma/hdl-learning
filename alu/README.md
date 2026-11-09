# ALU (Verilog)

An N-bit ALU in Verilog with Z/N/C/V status flags, verified with iverilog testbench.


## Implemented:
- 8 operations selected by a 3-bit opcode
- Width set by the WIDTH parameter
- Combinational (always @(*) with a case on the opcode)
- Zero, negative, carry/borrow and signed-overflow flags


## Opcodes
```
000  ADD   y = a + b
001  SUB   y = a - b
010  AND   y = a & b
011  OR    y = a | b
100  XOR   y = a ^ b
101  NOT   y = ~a
110  SHL   y = a << 1
111  SLT   y = 1 if a < b (signed), else 0
```

## Flags
```
Z is 1 when y is 0, for every operation.
N is the top bit of y, for every operation.
C is the carry-out for ADD and the borrow for SUB (x86 convention). It is 0 for all other operations.
V is set for ADD and SUB only, and is 0 for all other operations:
  ADD: V = (a[MSB] ~^ b[MSB]) & (a[MSB] ^ y[MSB])
  SUB: V = (a[MSB] ^ b[MSB]) & (a[MSB] ^ y[MSB])
```

Here. carry C is enabled for operations where bit length of the result exceeds the specified width (ADD) or a borrow where the unsigned result went below zero (SUB), and overflow V is enabled when operations that have 2 numbers with the same sign result in a different sign (ADD) and when the inputs have different signs(SUB). 
the reasoning behind having both C and V flags: the ALU doesnt know whether the numbers were intended as signed or unsigned, so the result can be correct for signed while wrong for unsigned and vice versa. this is the point of having both C and V flags to differentiate from the two situations


## Files

alu/rtl/alu.v      design
alu/tb/tb_alu.v    testbench
alu/README.md


## Run for testbench - 
```
    iverilog -Wall -o sim alu/rtl/alu.v alu/tb/tb_alu.v && vvp sim
    //runs the test
    verilator --lint-only -Wall alu/rtl/alu.v
    //lints RTL
    gtkwave alu.vcd
    //opens waveforms
```

## Verification


The testbench works by comparing each output to an expected value and counts the number of failures. edge cases were conducted for each operation including: carry, overflow, borrow, signed SLT, zeros, and default checks.

![Waveform of the directed tests](docs/waveform.png)
Synthesized structure (Yosys, after `proc; opt`): [alu_rtl.svg](synth/alu_rtl.svg)

## Results

- Directed tests: 18 / 18 passing
- Lint: clean
- Exhaustive test at 4 bits (cocotb): pending
- Random test at 32 bits (cocotb): pending
- Yosys cell count at WIDTH = 4 / 8 / 16: 
    124 / 243 / 485, about 30 cells per bit



## Design decisions and trade-offs
- could have incorporated a shift right operation, since the NOT op can be executed through XOR'ing with all 1's.
- Writing a + b / a - b and letting synthesis decide adder, rather than building ripple/lookahead adders.
- Chose borrow convention (x86) over not-borrow convention (ARM) so the carry flag is 1 when a subtraction operation go below zero. This was chosen since in verilog, extra top bit of subtraction comes out as one when it wraps below zero, so the simplest RTL was to just have {c, y}, as well as being more intuitive (c = 1) implies something out of the ordinary.

## Bugs
- SLT compared unsigned until $signed() was caught
    - the first version of SLT was y = (a <> b) ? 0 : 1, which when traced on an edge case like 1111 <> 0001, because verilog defaults to unsigned, read 1111 as 15. This meant the answer gave 0, which differed from my own result of 1 (-1 <> 1). This was eventually fixed by incorporating a $signed() operator on a and b. I learned that signed vs. unsigned is an interpretation that Verilog won’t apply for you, and every corner case I find by hand should become a test.
- put in the carry bit in subtraction as {y, c} instead of {c, y}.

## Next steps
- Registered inputs/outputs for timing, or running it through LibreLane.