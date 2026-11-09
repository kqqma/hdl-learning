# hdl-learning
My digital design portfolio: Verilog RTL, testbenches, and other hardware projects, built while working toward RTL/ASIC design.
Simulated with Icarus Verilog, viewed in GTKWave, linted with Verilator

## Tools
- **Icarus Verilog** for simulation
- **GTKWave** for waveform viewing
- **Verilator** for linting
- Developed on Ubuntu (WSL)

## Run a simulation
```bash
cd alu
iverilog -o sim rtl/*.v tb/*.v
vvp sim
gtkwave dump.vcd
