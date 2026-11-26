import os
DEPTH = int(os.environ.get("DEPTH", 4))   # default matches the RTL default
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles
import random
from collections import deque


@cocotb.test(skip=(DEPTH != 4))
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
@cocotb.test(skip=(DEPTH != 4))
async def idle_fifo(dut):
    # (push, pop, wr_data, exp_full, exp_empty, exp_rd_data or None)
    table = [(1, 0, 0x1, 0, 0, None), (1, 0, 0x2, 0, 0, None), (0, 0, 0,   0, 0, None), (0, 0, 0,   0, 0, None), (0, 0, 0,   0, 0, None), (0, 0, 0,   0, 0, None), (0, 0, 0,   0, 0, None), (0, 1, 0, 0, 0, 0x1), (0, 1, 0, 0, 1, 0x2)]

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

@cocotb.test()
async def empty_pop_fifo(dut):
    # (push, pop, wr_data, exp_full, exp_empty, exp_rd_data or None)
    table = [(0, 1, 0, 0, 1, None), 
            (0, 1, 0, 0, 1, None), 
            (0, 1, 0, 0, 1, None), 
            (1, 0, 0x1, 0, 0, None), 
            (0, 1, 0, 0, 1, 0x1), 
            (0, 1, 0, 0, 1, 0x1), 
            (1, 1, 0x2, 0, 0, 0x1), 
            (0, 1, 0, 0, 1, 0x2)]

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



@cocotb.test()
async def random_fifo(dut):
    model = deque()
    
    cycle = 0
    cyclefull = 0
    cycleempty = 0
    cyclepushblocked = 0
    cyclepopblocked = 0
    poppushfull = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk
    dut.reset.value = 1 # flashes the reset signal for 2 clock cycles to reset the DUT
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.reset.value = 0

    phases = [
        ("fill",     0.8, 0.2, 200),   # write-heavy: drives it to full
        ("drain",    0.2, 0.8, 200),   # read-heavy: drives it to empty
        ("balanced", 0.5, 0.5, 400),   # wanders around the middle
    ]
    for rep in range(5): #set an outer cycle
        for name, p_wr, p_rd, cycles in phases:
            for _ in range(cycles):
                cycle += 1
                #set probablility of wr_en and rd_en for randomness
                wr_en   = 1 if random.random() < p_wr else 0
                rd_en   = 1 if random.random() < p_rd else 0
                wr_data = random.randint(0, 255)   # any 8-bit value

                #read flags first, then decide push/pop ok
                full = int(dut.full.value)
                empty = int(dut.empty.value)
                pop_ok = (rd_en and not empty)
                push_ok = ((wr_en and not full) or (pop_ok and wr_en))
                #check to make sure every edge case actually happens
                if (full):
                    cyclefull += 1
                if (empty):
                    cycleempty += 1
                if (wr_en and not push_ok):
                    cyclepushblocked += 1
                if (rd_en and not pop_ok):
                    cyclepopblocked += 1
                if (full and push_ok and pop_ok):
                    poppushfull += 1
                #drive values
                dut.wr_en.value = wr_en
                dut.rd_en.value = rd_en
                dut.wr_data.value = wr_data
                #wait for edges
                await RisingEdge(dut.clk)
                await FallingEdge(dut.clk)
                #update values
                if (push_ok):
                    model.append(dut.wr_data.value)
                if (pop_ok):
                    assert dut.rd_data.value == model.popleft(), f"cycle {cycle}: read"

        dut._log.info(f"cycles={cycle} full={cyclefull} empty={cycleempty} "
                    f"push_blocked={cyclepushblocked} pop_blocked={cyclepopblocked} "
                    f"push+pop on full={poppushfull}")
        assert cyclefull > 0, "never reached full"
        assert cycleempty > 0, "never reached empty"
        assert cyclepushblocked > 0, "never pushed while full"
        assert cyclepopblocked > 0, "never popped while empty"
        assert poppushfull > 0, "never popped and pushed in same cycle while full"
            
            


        