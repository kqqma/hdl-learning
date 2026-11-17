import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

@cocotb.test()
async def test_moore_1011011(dut):
    """Test the Moore FSM with input sequence 1011011"""
    # Start the clock
    clock = Clock(dut.clk, 10, unit="ns")  # 10 ns period
    cocotb.start_soon(clock.start())

    await reset_fsm(dut)  
    # Define the input sequence and expected output sequence
    input_sequence = [1, 0, 1, 1, 0, 1, 1]
    for _ in range(1000):
        input_sequence.append(random.randint(0, 1))
    window = []
    matches = 0
    for i, bit in enumerate(input_sequence):              # CHANGED: enumerate here, replacing the old loop line
        await FallingEdge(dut.clk)
        getattr(dut, "in").value = bit
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")

        window = (window + [bit])[-4:]
        expected = 1 if window == [1, 0, 1, 1] else 0
        if expected == 1:                                  # NEW: count matches
            matches += 1

        assert dut.out.value == expected, f"bit #{i}: in={bit}, window={window}: got {int(dut.out.value)}, expected {expected}"
                                                           # CHANGED: no inner loop, {i} instead of (i)

    dut._log.info(f"{matches} matches in {len(input_sequence)} bits")   # NEW: after the loop
async def reset_fsm(dut):
    dut.reset.value = 1
    getattr(dut, "in").value = 0
    await ClockCycles(dut.clk, 2)
    await FallingEdge(dut.clk)
    dut.reset.value = 0