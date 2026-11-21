import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer, with_timeout
import random
CLK_FREQ = 50_000_000
BAUD = 115_200
oversample = 1
expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

async def send_byte(dut, byte, div): 

    dut.rx.value = 0
    await ClockCycles(dut.clk, div)  # Wait for start bit

    for i in range(8):
        dut.rx.value = (byte >> i) & 1
        await ClockCycles(dut.clk, div) 
    
    dut.rx.value = 1
    await ClockCycles(dut.clk, div) # wait for stop bit

async def wait_for_byte(dut):
    await RisingEdge(dut.rx_valid) # watch for the pulse
    await FallingEdge(dut.clk) # wait for settle
    return int(dut.rx_data.value) # grab the byte

@cocotb.test()
async def receive_bytes(dut):

    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk
    dut.rx.value = 1 # set rx before reset
    dut.resetn.value = 0 # flashes reset low
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)


    rx_task = cocotb.start_soon(wait_for_byte(dut)) # sets up a listener that waits at rising edge of rx_valid and when pulse comes, reads rx data and finishes.
    await send_byte(dut, 0x41, expected_div) # then send 0x41 into send_byte function.
    got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
    assert got == 0x41, f"sent 0x41, received {got:#04x}" # check the got value

@cocotb.test()
async def receive_random_bytes(dut):

    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk

    dut.resetn.value = 0 # flashes the reset signal low for 2 clock cycles to reset the DUT
    dut.rx.value = 1 # set rx before reset
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)


    
    for i in range(256):
        #repeat 256 times, byte i
        await ClockCycles(dut.clk, random.randint(1, expected_div))   # random idle time, rx stays high - for constrained random verification

        rx_task = cocotb.start_soon(wait_for_byte(dut)) # sets up a listener that waits at rising edge of rx_valid and when pulse comes, reads rx data and finishes.
        await send_byte(dut, i, expected_div) # wait for send_byte to send i byte into the rx line
        got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
        assert got == i, f"sent {i:#04x}, received {got:#04x}" # check the got value