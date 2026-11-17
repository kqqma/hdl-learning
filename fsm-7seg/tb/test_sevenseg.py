import cocotb
from cocotb.triggers import Timer
def segmodel(hex_digit):
    seg = 0b0000000
    if hex_digit == 0x0:
        seg = 0b0111111
    elif hex_digit == 0x1:
        seg = 0b0000110
    elif hex_digit == 0x2:
        seg = 0b1011011
    elif hex_digit == 0x3:
        seg = 0b1001111
    elif hex_digit == 0x4:
        seg = 0b1100110
    elif hex_digit == 0x5:
        seg = 0b1101101
    elif hex_digit == 0x6:
        seg = 0b1111101
    elif hex_digit == 0x7:
        seg = 0b0000111
    elif hex_digit == 0x8:
        seg = 0b1111111
    elif hex_digit == 0x9:
        seg = 0b1100111
    elif hex_digit == 0xa:
        seg = 0b1110111
    elif hex_digit == 0xb:
        seg = 0b1111100
    elif hex_digit == 0xc:
        seg = 0b0111001
    elif hex_digit == 0xd:
        seg = 0b1011110
    elif hex_digit == 0xe:
        seg = 0b1111001
    elif hex_digit == 0xf:
        seg = 0b1110001
    else:
        raise ValueError("Invalid hexadecimal digit")
    
    return seg

@cocotb.test()
async def test_exhaustive(dut):

    for a in range(16):
        getattr(dut, "in").value = a
        await Timer(1, unit="ns")
        expected_seg = segmodel(a)
        assert dut.out.value == expected_seg, f"seg: got {int(dut.out.value):07b}, expected {expected_seg:07b} (hex_digit={a:X})"