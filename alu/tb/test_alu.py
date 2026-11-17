import cocotb
from cocotb.triggers import Timer
def to_signed(x):
        if ((x >> 3) & 1) == 1:
            return x - 16
        else:
            return x
        
def alu_model(a, b, op):
    y = c = v = 0
    if op == 0b000:
        y= a + b
        c = (y >> 4) & 1
        v = ((((a>>3) & 1) == ((b>>3) & 1)) and ((y>>3) & 1) != (a>>3) & 1)
    elif op == 0b001:
        y= a - b
        c = (y >> 4) & 1
        v = ((((a>>3) & 1) != ((b>>3) & 1)) and ((y>>3) & 1) != (a>>3) & 1)
    elif op == 0b010:
        y= a & b
    elif op == 0b011:
        y= a | b
    elif op == 0b100:
        y= a ^ b
    elif op == 0b101:
        y= ~a
    elif op == 0b110:
        y= a << 1
    elif op == 0b111:
        y = (to_signed(a) < to_signed(b))
    else:
        raise ValueError("Invalid operation code")
    cy = y & 0b1111  # Ensure y is 4 bits
    z = (cy == 0)

    n = (cy >> 3) & 1
    return (cy, int(z), n, c, int(v))
    

@cocotb.test()
async def test_exhaustive(dut):

    for op in range (8):
        for a in range (16):
            for b in range (16):
                dut.a.value = a
                dut.b.value = b
                dut.op.value = op
                await Timer(1, unit="ns")
                expected_y, expected_z, expected_n, expected_c, expected_v = alu_model(a, b, op)
                assert dut.y.value == expected_y, f"y: got {int(dut.y.value)}, expected {expected_y} (a={a}, b={b}, op={op:03b})"
                assert dut.z.value == expected_z, f"z: got {int(dut.z.value)}, expected {expected_z} (a={a}, b={b}, op={op:03b})"
                assert dut.n.value == expected_n, f"n: got {int(dut.n.value)}, expected {expected_n} (a={a}, b={b}, op={op:03b})"
                assert dut.c.value == expected_c, f"c: got {int(dut.c.value)}, expected {expected_c} (a={a}, b={b}, op={op:03b})"
                assert dut.v.value == expected_v, f"v: got {int(dut.v.value)}, expected {expected_v} (a={a}, b={b}, op={op:03b})"