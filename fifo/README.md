# Synchronous FIFO

Parameterized single-clock FIFO in SystemVerilog, verified with cocotb.

## Status
- [x] Paper design + cycle table
- [x] RTL (Verilator `-Wall` lint clean)
- [x] Directed cocotb test (cycle table, 10 cycles)
- [ ] Bug-catcher tests (idle, pop while empty)
- [ ] DEPTH = 1 and 2
- [ ] Random scoreboard test
- [ ] Results

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
- Read latency: registered read. `rd_data` shows the popped word one cycle after `rd_en`.

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
- `tb/test_fifo.py`: table-driven directed test that replays the cycle table above and checks `full`, `empty` and `rd_data` every cycle.
- Run: `cd tb && make` (cocotb + Icarus Verilog)

## Trade-offs
- Push-on-full allowed with a simultaneous pop: one extra term in the write guard, and no dropped data. On the same edge, the read gets the old word (A) while the write stores the new one (F).
- Pop-on-empty with a simultaneous push is not allowed: the registered read would sample the slot before the new word lands. Supporting it would need a bypass path.

## Bug story

### Proving each test can fail
Each directed test was checked by breaking the RTL on purpose and confirming the test fails where expected:

| Test | RTL broken by | Caught at |
|------|---------------|-----------|
| `test_fifo` (cycle table) | No full guard: `push = wr_en` | Cycle 5, `rd_data`: the push while full overwrote A in slot 0 |
| `idle_fifo` | `wr_ptr` advances every cycle, not only on push | Row 4, `full`: a 2-item FIFO reported full after the pointer drifted a whole lap |
| `empty_pop_fifo` | No empty guard: `pop = rd_en` | Row 1, `empty`: the first pop from reset moved `rd_ptr` past `wr_ptr`, so an empty FIFO reported 3 junk items |

Each bug was invisible to the other two tests, since a test only catches what it exercises.

### Non-power-of-2 DEPTH silently lost data
Running with `DEPTH = 3` before any parameter check: `$clog2(3) = 2`, so the pointers counted as if there were 4 slots, but `mem` only had 3. The 4th push (D) went to `mem[3]`, which doesn't exist, so the write was silently dropped, and `full` only went high after 4 pushes. The read at cycle 9 returned `XXXXXXXX` instead of D. Two of the three tests still passed at this depth.

`DEPTH = 1` had a different problem: `AW = 0` made `wr_ptr[AW-1:0]` into `wr_ptr[-1:0]`, which failed to compile with a confusing part-select error.

**Fix:** an elaboration-time check that stops the simulation at time 0 with a clear message:

    initial begin
        if (DEPTH < 2 || ((DEPTH & (DEPTH-1)) != 0))
            $fatal(1, "sync_fifo: DEPTH must be a power of 2 and >= 2");
    end

plus `AW = (DEPTH > 1) ? $clog2(DEPTH) : 1` so `DEPTH = 1` compiles far enough to reach the message.

## Results
(Fill in: number of random transactions, depths tested, synthesis cell/FF counts.)