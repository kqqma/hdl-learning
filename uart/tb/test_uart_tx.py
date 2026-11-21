import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer, with_timeout
import random
CLK_FREQ = 50_000_000
BAUD = 115_200
oversample = 1
expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

async def receive_byte(dut, div):
    
    await FallingEdge(dut.tx)  # Wait for start bit
    
    # TODO 2: wait div // 2 clock cycles, check tx == 0 (start bit)
    await ClockCycles(dut.clk, div // 2)
    assert dut.tx.value == 0, "start bit not low at midpoint"
    byte = 0
    # TODO 3: 8 times: wait div cycles, read tx, build the byte LSB first
    for i in range(8):
        await ClockCycles(dut.clk, div)
        bit = int(dut.tx.value)
        byte |= (bit << i)

    await ClockCycles(dut.clk, div)
    assert dut.tx.value == 1

    return byte

@cocotb.test()
async def send_bytes(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # 50 MHz

    dut.resetn.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1

    rx_task = cocotb.start_soon(receive_byte(dut, expected_div))

    await FallingEdge(dut.clk)
    dut.tx_data.value = 0x41
    dut.tx_start.value = 1
    await FallingEdge(dut.clk)
    dut.tx_start.value = 0
    got_byte = await rx_task
    assert got_byte == 0x41, f"Expected 0x41, got {got_byte:#04x}"

@cocotb.test()
async def send_random_bytes(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # 50 MHz
    dut.resetn.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1


    
    for i in range(256):
        dut._log.info(f"sending {i:#04x}")
        await ClockCycles(dut.clk, random.randint(1, expected_div))  # random delay before sending
        rx_task = cocotb.start_soon(receive_byte(dut, expected_div))
        await FallingEdge(dut.clk)
        dut.tx_data.value = i
        dut.tx_start.value = 1
        await FallingEdge(dut.clk)
        dut.tx_start.value = 0
        got_byte = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns")
        assert got_byte == i, f"Expected {i:#04x}, got {got_byte:#04x}"
        while dut.tx_busy.value == 1:
            await FallingEdge(dut.clk)
