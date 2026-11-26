
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles



@cocotb.test()
async def test_fifo(dut):
    table = [(1, 0, 0xA, 0, 0, None), (1, 0, 0xB, 0, 0, None), (1, 0, 0xC, 0, 0, None), (1, 0, 0xD, 1, 0, None), (1, 0, 0xE, 1, 0, None), (1, 1, 0xF, 1, 0, 0xA), (0, 1, 0, 0, 0, 0xB), (0, 1, 0, 0, 0, 0xC), (0, 1, 0, 0, 0, 0xD), (0, 1, 0, 0, 1, 0xF)]

    dut.wr_en.value = 0
    dut.rd_en.value = 0
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk
    dut.reset.value = 1 # flashes the reset signal for 2 clock cycles to reset the DUT
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.reset.value = 0

    for cycle, (push, pop, wdata, exp_full, exp_empty, exp_rd) in enumerate(table, start=1):
        dut.wr_en.value = push
        dut.rd_en.value = pop
        dut.wr_data.value = wdata
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        assert dut.full.value  == exp_full,  f"cycle {cycle}: full"
        assert dut.empty.value == exp_empty, f"cycle {cycle}: empty"
        if (exp_rd is not None):
            assert dut.rd_data.value == exp_rd, f"cycle {cycle}: read"
        