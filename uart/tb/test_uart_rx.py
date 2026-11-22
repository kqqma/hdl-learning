import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer, with_timeout
import random
CLK_FREQ = 50_000_000
BAUD = 115_200
oversample = 1
expected_div = (CLK_FREQ + (BAUD * oversample) //2) // (BAUD * oversample)

async def send_byte(dut, byte, div, stop=1):
    dut.rx.value = 0 # send start bit
    await ClockCycles(dut.clk, div)
    for i in range(8): 
        dut.rx.value = (byte >> i) & 1 # data bits, where LSB first
        await ClockCycles(dut.clk, div)
    dut.rx.value = stop # send stop bit, normally one, but set to 0 to test frame error detection
    await ClockCycles(dut.clk, div)

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
    counts = {"valid": 0, "err": 0} # dictionary to store the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(count_pulses(dut, counts)) # start a task that counts the number of pulses on rx_valid and frame_err.
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

    # after the for loop ends:
    assert counts["valid"] == 256, f"expected 256 rx_valid pulses, got {counts['valid']}"
    assert counts["err"] == 0, f"expected no frame errors, got {counts['err']}"

@cocotb.test()
async def bad_stop_bit(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.rx.value = 1
    dut.resetn.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)

    counts = {"valid": 0, "err": 0}
    cocotb.start_soon(count_pulses(dut, counts))    # start counting before anything happens

    # 1. send a broken frame
    await send_byte(dut, 0x55, expected_div, stop=0)
    dut.rx.value = 1                                 # send_byte left the line LOW, so put it back to idle
    await ClockCycles(dut.clk, 12 * expected_div)    # idle long enough for RX to finish whatever it's doing

    # 2. RX should have flagged the error and NOT reported a byte
    assert counts["err"] == 1, f"expected 1 frame_err, got {counts['err']}"
    assert counts["valid"] == 0, f"expected no rx_valid, got {counts['valid']}"

    # 3. RX should still work for the next good frame
    rx_task = cocotb.start_soon(wait_for_byte(dut))
    await send_byte(dut, 0xA3, expected_div)
    got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns")
    assert got == 0xA3, f"after the bad frame, sent 0xA3, received {got:#04x}"

    
@cocotb.test()
async def glitch_rejected_rx_low(dut):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
    dut.rx.value = 1
    dut.resetn.value = 0
    await ClockCycles(dut.clk, 2)
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)

    counts = {"valid": 0, "err": 0}
    cocotb.start_soon(count_pulses(dut, counts))    # start counting before anything happens

    #pull rx low for 50 cycles to simulate a a short glitch 
    dut.rx.value = 0
    await ClockCycles(dut.clk, 50)
    dut.rx.value = 1 #simulate glitch recovered return rx to idle

    await ClockCycles(dut.clk, 3 * expected_div)
    # 2. RX should have ignored glitch 
    assert counts["err"] == 0, f"expected 1 frame_err, got {counts['err']}"
    assert counts["valid"] == 0, f"expected no rx_valid, got {counts['valid']}"

    # 3. RX should still work for the next good frame
    rx_task = cocotb.start_soon(wait_for_byte(dut))
    await send_byte(dut, 0xA3, expected_div)
    got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns")
    assert got == 0xA3, f"after the bad frame, sent 0xA3, received {got:#04x}"

    
@cocotb.test()
async def baud_mismatch_test(dut):
    counts = {"valid": 0, "err": 0} # dictionary to store the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(count_pulses(dut, counts)) # start a task that counts the number of pulses on rx_valid and frame_err.
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
        await send_byte(dut, i, 443) # wait for send_byte to send i byte into the rx line
        got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
        assert got == i, f"sent {i:#04x}, received {got:#04x}" # check the got value

        rx_task = cocotb.start_soon(wait_for_byte(dut)) # sets up a listener that waits at rising edge of rx_valid and when pulse comes, reads rx data and finishes.
        await send_byte(dut, i, 425) # wait for send_byte to send i byte into the rx line
        got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
        assert got == i, f"sent {i:#04x}, received {got:#04x}" # check the got value

    # after the for loop ends:
    assert counts["valid"] == 512, f"expected 512 rx_valid pulses, got {counts['valid']}"
    assert counts["err"] == 0, f"expected no frame errors, got {counts['err']}"

@cocotb.test()
async def receive_backtoback_bytes(dut):
    counts = {"valid": 0, "err": 0} # dictionary to store the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(count_pulses(dut, counts)) # start a task that counts the number of pulses on rx_valid and frame_err.
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())  # instantiate a 50 MHz clock on dut.clk

    dut.resetn.value = 0 # flashes the reset signal low for 2 clock cycles to reset the DUT
    dut.rx.value = 1 # set rx before reset
    await ClockCycles(dut.clk, 2) #waits for 2 clock cycles to ensure the reset is applied
    dut.resetn.value = 1
    await ClockCycles(dut.clk, 2)


    
    for i in range(256):
        #repeat 256 times, byte i
        #no idle time here
        rx_task = cocotb.start_soon(wait_for_byte(dut)) # sets up a listener that waits at rising edge of rx_valid and when pulse comes, reads rx data and finishes.
        await send_byte(dut, i, expected_div) # wait for send_byte to send i byte into the rx line
        got = await with_timeout(rx_task, 2 * 10 * expected_div * 20, "ns") # wait until listener is done, and then see what it returned
        assert got == i, f"sent {i:#04x}, received {got:#04x}" # check the got value

    # after the for loop ends:
    assert counts["valid"] == 256, f"expected 256 rx_valid pulses, got {counts['valid']}"
    assert counts["err"] == 0, f"expected no frame errors, got {counts['err']}"
