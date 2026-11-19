import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer

CLK_FREQ = 50_000_000
BAUD = 115_200

@cocotb.test()
async def tick_period(dut):
    oversample = int(os.environ.get("OVERSAMPLE", "1"))
# TODO: same rounding formula as your RTL, in Python (use // for integer division)
    expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # 50 MHz

    dut.resetn.value = 0
    dut.clear.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1

    tick_cycles = []
    for cycle in range(expected_div * 5):
        await FallingEdge(dut.clk)    # sample mid-cycle, after everything has settled
        if dut.tick.value == 1:
            tick_cycles.append(cycle)

    # TODO: check there were at least a few ticks
    assert len(tick_cycles) >= 3, f"Expected at least 3 ticks, got {len(tick_cycles)}"
    # TODO: check every gap between consecutive entries == expected_div
    for i in range(1, len(tick_cycles)):
        gap = tick_cycles[i] - tick_cycles[i-1]
        assert gap == expected_div, f"Gap {i}: expected {expected_div}, got {gap}"



@cocotb.test()
async def clear_restarts_count(dut):
    oversample = int(os.environ.get("OVERSAMPLE", "1"))
    expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())

    dut.resetn.value = 0
    dut.clear.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1

    await ClockCycles(dut.clk, 16)

    # pulse clear for exactly one cycle
    await FallingEdge(dut.clk)
    dut.clear.value = 1
    await FallingEdge(dut.clk)
    dut.clear.value = 0
    count = 0
    while True:
        count += 1
        assert count <= 2 * expected_div, "tick never came after clear"
        if dut.tick.value == 1:
            break
        await FallingEdge(dut.clk)
    # Loop counts from the edge where clear was applied, so the period is exactly DIV.
    assert count == expected_div, f"Expected {expected_div} cycles until tick after clear, got {count}"