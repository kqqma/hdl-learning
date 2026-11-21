import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer, with_timeout
import random
CLK_FREQ = 50_000_000
BAUD = 115_200
oversample = 1
expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

async def wait_for_byte(dut):
    await RisingEdge(dut.rx_valid) # watch for the pulse
    await FallingEdge(dut.clk) # wait for settle
    return int(dut.rx_data.value) # grab the byte

async def count_pulses(dut, counts): # checks the number of pulses on rx_valid and frame_err.
    while True:
        await FallingEdge(dut.clk)
        if dut.rx_valid.value == 1:
            counts["valid"] += 1
        if dut.frame_err.value == 1:
            counts["err"] += 1
@cocotb.test()
async def send_and_receive_random_bytes(dut):
    counts = {"valid": 0, "err": 0} # dictionary to store the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(count_pulses(dut, counts)) # start a task that counts the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk

    dut.resetn.value = 0 # flashes the reset signal low for 2 clock cycles to reset the DUT
    await FallingEdge(dut.clk)
    dut.tx_start.value = 0 #instantiates tx_start, tx_data so not left in unknown
    dut.tx_data.value = 0
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)


    for i in range(256):
        await ClockCycles(dut.clk, random.randint(1, expected_div)) # wait a random number of cycles 
        await FallingEdge(dut.clk)
        
        rx_task = cocotb.start_soon(wait_for_byte(dut)) # sets up a listener that waits at rising edge of rx_valid and when pulse comes, reads rx data and finishes.
        dut.tx_data.value = i # send the byte
        dut.tx_start.value = 1
        await FallingEdge(dut.clk)
        dut.tx_start.value = 0

        got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
        #python waits here while hardware sends all 10 bits (start, 8 data, stop) at the baud rate, and then waits for the rx_valid pulse to come back
        assert got == i, f"sent {i:#04x}, received {got:#04x}" # check the got value
        while (dut.tx_busy.value == 1):
            await FallingEdge(dut.clk) # wait for tx_busy to go low before sending the next byte

    assert counts["valid"] == 256, f"expected 256 rx_valid pulses, got {counts['valid']}"
    assert counts["err"] == 0, f"expected no frame errors, got {counts['err']}"