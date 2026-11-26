# Synchronous FIFO

Parameterized single-clock FIFO in SystemVerilog, verified with cocotb.

## Interface
| Signal  | Dir | Description |
|---------|-----|-------------|
| clk     | in  | Clock |
| reset   | in  | Synchronous reset, active high |
| wr_en   | in  | Push request |
| wr_data | in  | Data to push (WIDTH bits) |
| full    | out | FIFO is full |
| rd_en   | in  | Pop request |
| rd_data | out | Popped data, valid the cycle after rd_en |
| empty   | out | FIFO is empty |

Parameters: `DEPTH` (default 4, must be a power of 2 and >= 2, enforced by `$fatal`), `WIDTH` (default 8).

## Design
- Memory: `DEPTH` slots of `WIDTH` bits.
- `AW = $clog2(DEPTH)` address bits. Pointers are `AW+1` bits wide: the bottom `AW` bits are the address, the top bit flips each time the pointer wraps.
- State (flip-flops): `mem`, `wr_ptr`, `rd_ptr`, `rd_data`
- Combinational: `full`, `empty`, `push`, `pop`
- `wr_en` / `rd_en` are requests; `push` / `pop` are the accepted operations. Only `push` / `pop` move the pointers or touch memory.

### Full / empty
    empty = (wr_ptr == rd_ptr);
    full  = (wr_ptr[AW-1:0] == rd_ptr[AW-1:0]) && (wr_ptr[AW] != rd_ptr[AW]);

Same slot and same lap → empty. Same slot, writer one lap ahead → full.

### Policies
- Push while full: blocked, unless a pop happens in the same cycle.
- Pop while empty: blocked, even if a push happens in the same cycle.
- Read latency: registered read. `rd_data` shows the popped word one cycle after `rd_en`, and holds its value on cycles with no accepted pop.

## Cycle table (DEPTH = 4)
| Cycle | push | pop | wr_data | wr_ptr | rd_ptr | full | empty | rd_data |
|-------|------|-----|---------|--------|--------|------|-------|---------|
| reset | 0 | 0 | – | 000 | 000 | 0 | 1 | – |
| 1  | 1 | 0 | A | 001 | 000 | 0 | 0 | – |
| 2  | 1 | 0 | B | 010 | 000 | 0 | 0 | – |
| 3  | 1 | 0 | C | 011 | 000 | 0 | 0 | – |
| 4  | 1 | 0 | D | 100 | 000 | 1 | 0 | – |
| 5  | 1 | 0 | E (dropped) | 100 | 000 | 1 | 0 | – |
| 6  | 1 | 1 | F | 101 | 001 | 1 | 0 | A |
| 7  | 0 | 1 | – | 101 | 010 | 0 | 0 | B |
| 8  | 0 | 1 | – | 101 | 011 | 0 | 0 | C |
| 9  | 0 | 1 | – | 101 | 100 | 0 | 0 | D |
| 10 | 0 | 1 | – | 101 | 101 | 0 | 1 | F |

## Verification
All tests are in `tb/test_fifo.py` (cocotb + Icarus Verilog).

| Test | What it checks | Depths |
|------|----------------|--------|
| `test_fifo` | Replays the cycle table above row by row, checking `full`, `empty` and `rd_data` every cycle | 4 |
| `idle_fifo` | Push 2, idle 5 cycles, pop 2: nothing moves without an enable | 4 |
| `empty_pop_fifo` | Pops from empty are blocked (`rd_data` holds); push + pop on empty accepts only the push | 2, 4 |
| `random_fifo` | 4,000 random cycles against a Python `deque` model, in repeated fill / drain / balanced phases, with coverage counters | 2, 4 |

The random test drives raw random requests (including pushes while full and pops while empty) and predicts acceptance from `full` / `empty` sampled before each clock edge, using the same policy as the spec. The directed tests use hand-checked expected values, which guards against the model and the RTL sharing the same mistake.

Run:

    cd tb
    make                  # DEPTH = 4 (default)
    make clean && make DEPTH=2

`test_fifo` and `idle_fifo` are written for 4 slots, so they are skipped at other depths.

## Results

All tests pass at DEPTH = 2 and DEPTH = 4. DEPTH = 1 and 3 are rejected at time 0 by the `$fatal` parameter check.

Random-test coverage (4,000 cycles each):

| Event | DEPTH = 4 | DEPTH = 2 |
|-------|-----------|-----------|
| Cycles full | 1,295 | 1,747 |
| Cycles empty | 1,033 | 1,112 |
| Push blocked (full, no pop) | 698 | 756 |
| Pop blocked (empty) | 692 | 761 |
| Push + pop on full | 242 | 374 |

The test asserts every count is above zero, so a change that stops it from reaching an edge case fails the run.

With the same traffic, the 2-slot FIFO spends more time full (1,747 vs. 1,295 cycles) and sees more push + pop on full: there is less room to absorb a burst of writes, so backpressure happens more often. This is the depth-sizing trade-off in numbers.

### Synthesis (Yosys `synth`, generic gates, WIDTH = 8)

| DEPTH | Flip-flops | 2:1 muxes | Other logic | Total cells |
|-------|-----------|-----------|-------------|-------------|
| 4  | 46  | 24  | 27 | 97  |
| 8  | 80  | 56  | 47 | 183 |
| 16 | 146 | 120 | 72 | 338 |

Flip-flops = DEPTH × WIDTH (`mem`) + 2 × (log2(DEPTH) + 1) (pointers) + WIDTH (`rd_data`).
The read mux is (DEPTH − 1) × WIDTH 2:1 muxes. Both predictions matched Yosys exactly at all three depths.

Only the pointers have reset flip-flops (`$_SDFFE_`); `mem` and `rd_data` are not reset, so they use cheaper `$_DFFE_` cells.
Storage + read mux grow linearly with DEPTH and are 72–79% of all cells, which is why large FIFOs use block RAM instead of flip-flops.

Reports: `synth/fifo_d4.txt`, `synth/fifo_d8.txt`, `synth/fifo_d16.txt`.


## Trade-offs
- Push-on-full allowed with a simultaneous pop: one extra term in the write guard, and no dropped data. On the same edge, the read gets the old word (A) while the write stores the new one (F).
- Pop-on-empty with a simultaneous push is not allowed: the registered read would sample the slot before the new word lands. Supporting it would need a bypass path.
- Power-of-2 depths only: lets the pointers wrap for free by truncation and keeps full/empty to a simple compare. Other depths would need explicit wrap logic.

## Bug story

### Proving each test can fail
Each test was checked by breaking the RTL on purpose and confirming the test fails where expected:

| Test | RTL broken by | Caught at |
|------|---------------|-----------|
| `test_fifo` (cycle table) | No full guard: `push = wr_en` | Cycle 5, `rd_data`: the push while full overwrote A in slot 0 |
| `idle_fifo` | `wr_ptr` advances every cycle, not only on push | Row 4, `full`: a 2-item FIFO reported full after the pointer drifted a whole lap |
| `empty_pop_fifo` | No empty guard: `pop = rd_en` | Row 1, `empty`: the first pop from reset moved `rd_ptr` past `wr_ptr`, so an empty FIFO reported 3 junk items |
| `random_fifo` | Push guard without `\|\| pop` (push + pop on full no longer allowed) | Cycle 19 (DEPTH = 2): the read returned `0x2C`, which was the model's *next* value, so the RTL had dropped `0xA2` that the model expected |

Each directed bug was invisible to the other directed tests, since a test only catches what it exercises. Spotting that the actual value equals the model's next expected value is the giveaway for a dropped write.

### Non-power-of-2 DEPTH silently lost data
Running with `DEPTH = 3` before any parameter check: `$clog2(3) = 2`, so the pointers counted as if there were 4 slots, but `mem` only had 3. The 4th push (D) went to `mem[3]`, which doesn't exist, so the write was silently dropped, and `full` only went high after 4 pushes. The read at cycle 9 returned `XXXXXXXX` instead of D. Two of the three tests at the time still passed at this depth.

`DEPTH = 1` had a different problem: `AW = 0` made `wr_ptr[AW-1:0]` into `wr_ptr[-1:0]`, which failed to compile with a confusing part-select error.

**Fix:** a check that stops the simulation at time 0 with a clear message:

    initial begin
        if (DEPTH < 2 || ((DEPTH & (DEPTH-1)) != 0))
            $fatal(1, "sync_fifo: DEPTH must be a power of 2 and >= 2");
    end

plus `AW = (DEPTH > 1) ? $clog2(DEPTH) : 1` so `DEPTH = 1` compiles far enough to reach the message.

### A misplaced `end` that no test caught
During a refactor, an extra `end` closed the reset `else` early, so the pop logic ran even while `reset` was high. All tests still passed, because every test holds `rd_en = 0` during reset. Found in code review and fixed by re-indenting the `always_ff` block. A reset-mid-traffic test would catch this class of bug and is a candidate for future work.