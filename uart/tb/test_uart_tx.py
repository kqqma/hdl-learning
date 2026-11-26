import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer, with_timeout
import random
CLK_FREQ = 50_000_000
BAUD = 115_200
oversample = 1
expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

async def receive_byte(dut, div): #no cocotb function. is called in send bytes and send random bytes
    
    await FallingEdge(dut.tx)  # Wait for start bit
    
    await ClockCycles(dut.clk, div // 2) # wait half a clock cycle (434/2 = 217 cycles) to sample first bit
    assert dut.tx.value == 0, "start bit not low at midpoint" # check start bit not low
    byte = 0 # empty byte to store received bits

    for i in range(8):
        #moves forward one full cycle to the middle of the next bit
        await ClockCycles(dut.clk, div)
        bit = int(dut.tx.value) # reads tx value and stores it in bit at position i
        byte |= (bit << i)

    await ClockCycles(dut.clk, div) # one more cycle forward to the stop bit
    assert dut.tx.value == 1 # check for the stop bit which must be high

    return byte #hands back the received byte to the calling function (value that got_byte in rx_task = await receive_byte(dut, expected_div) will store)

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

    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk

    dut.resetn.value = 0 # flashes the reset signal low for 2 clock cycles to reset the DUT
    dut.tx_start.value = 0 #instantiates tx_start, and tx_data, so they are not left in an unknown state
    dut.tx_data.value = 0
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.resetn.value = 1


    
    for i in range(256):
        #repeat 256 times, sending a random byte
        await ClockCycles(dut.clk, random.randint(1, expected_div))  # random delay before sending
        rx_task = cocotb.start_soon(receive_byte(dut, expected_div)) #start a python receiver in background - waits at falling edge for start bit
      
        await FallingEdge(dut.clk) #moves to falling edge (clock cycles used rising edges)
        dut.tx_data.value = i #byte i on the data input and raises tx_start
        dut.tx_start.value = 1
        await FallingEdge(dut.clk) # one full cycle of tx_start high, then low again
        dut.tx_start.value = 0

        got_byte = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # waits for receiver to finish and stores byte in got_byte. timeout is safety net of 2x a frame
        assert got_byte == i, f"Expected {i:#04x}, got {got_byte:#04x}" # check if got_byte matches the sent byte i, if not, raise an assertion error with the expected and got values
        
        while dut.tx_busy.value == 1: # wait for tx to completely finish before sending the next byte
            await FallingEdge(dut.clk)
