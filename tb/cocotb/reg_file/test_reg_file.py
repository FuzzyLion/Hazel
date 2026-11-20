import cocotb
from cocotb.clock import Clock, Timer
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly

from reg_file_model import RegFileModel

import random
import os

@cocotb.test()
async def test_reg_file(dut):

#    model = RegFileModel()

    dut.clk.value = 0
    dut.reset.value = 1
    dut.rf_write_W.value = 0
    dut.rs1_idx_rf.value = 0
    dut.rs2_idx_rf.value = 0
    dut.rd_idx_W.value = 0
    dut.WB_mux_result.value = 0

    clock = Clock(dut.clk, 1, unit="ns")
    clock.start(start_high=False)

    await RisingEdge(dut.clk)

    # Initialization test
    for idx in range(1, 32):
        await FallingEdge(dut.clk)
        dut.reset.value = 0
        dut.rf_write_W.value = 1
        dut.rd_idx_W.value = idx
        dut.WB_mux_result.value = 0xFFFF_FFFF
        
        await RisingEdge(dut.clk)
        
        await FallingEdge(dut.clk)
        dut.rf_write_W.value = 0
        dut.rs1_idx_rf.value = idx
        
        await ReadOnly()
        
        actual_rs1 = int(dut.rs1_val_D.value)
        assert actual_rs1 == 0xFFFF_FFFF, (
            f"Write failed: rs1 x{idx} expected 0xFFFF_FFFF, got {actual_rs1}"
        )
        
    await FallingEdge(dut.clk)
    dut.reset.value = 1
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    
    for idx in range(32):
        await FallingEdge(dut.clk)
        dut.rs1_idx_rf.value = idx
        dut.rs2_idx_rf.value = 31 - idx

        await ReadOnly()

        actual_rs1 = int(dut.rs1_val_D.value)
        actual_rs2 = int(dut.rs2_val_D.value)
        assert actual_rs1 == 0, (
            f"Reset failed: rs1 x{idx} expected 0, got {actual_rs1}"
        )
        assert actual_rs2 == 0, (
            f"Reset failed: rs2 x{31 - idx} expected 0, got {actual_rs2}"
        )

    # Synchronous Write
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.rf_write_W.value = 1
    dut.rd_idx_W.value = 2
    dut.WB_mux_result.value = 100

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0
    dut.rs1_idx_rf.value = 2

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    assert actual_rs1 == 100, (
        f"Synchronous write failed: rs1 x{dut.rs1_idx_rf.value} expected 100, got {actual_rs1}"
    )

    # Combinational Read
    await FallingEdge(dut.clk)
    dut.rd_idx_W.value = 3
    dut.rf_write_W.value = 1
    dut.WB_mux_result.value = 200
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0 
    dut.rs1_idx_rf.value = 2 
    dut.rs2_idx_rf.value = 3 

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 100, (
        f"Combinational read failed: rs1 x{dut.rs1_idx_rf.value} expected 100, got {actual_rs1}"
    )
    assert actual_rs2 == 200, (
        f"Combinational read failed: rs2 x{dut.rs2_idx_rf.value} expected 200, got {actual_rs2}"
    )
    
    await FallingEdge(dut.clk)
    dut.rs1_idx_rf.value = 3 
    dut.rs2_idx_rf.value = 2 

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 200, (
        f"Synchronous write failed: rs1 x{dut.rs1_idx_rf.value} expected 200, got {actual_rs1}"
    )
    assert actual_rs2 == 100, (
        f"Synchronous write failed: rs2 x{dut.rs2_idx_rf.value} expected 100, got {actual_rs2}"
    )

    # Test Bypass
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 1 
    dut.rd_idx_W.value = 7 
    dut.WB_mux_result.value = 20 

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0 # When rf_write = 0, bypass will not activate
    dut.rs1_idx_rf.value = 7
    dut.rs2_idx_rf.value = 7
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 30

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 20, (
        f"Bypass-disable failed: rs1 x{dut.rs1_idx_rf.value} expected 20, got {actual_rs1}"
    )
    assert actual_rs2 == 20, (
        f"Bypass-disable failed: rs2 x{dut.rs2_idx_rf.value} expected 20, got {actual_rs2}"
    )

    await Timer(100, unit="ps")

    dut.rf_write_W.value = 1 # When rf_write = 1, bypass will activate
    dut.rs1_idx_rf.value = 7
    dut.rs2_idx_rf.value = 7
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 30

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 30, (
        f"Bypass failed: rs1 x{dut.rs1_idx_rf.value} expected 30, got {actual_rs1}"
    )
    assert actual_rs2 == 30, (
        f"Bypass failed: rs2 x{dut.rs2_idx_rf.value} expected 30, got {actual_rs2}"
    )

    # x0 Priority Check
    await FallingEdge(dut.clk)
    dut.rd_idx_W.value = 0
    dut.WB_mux_result.value = 50

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rs1_idx_rf.value = 0
    dut.rs2_idx_rf.value = 0

    await ReadOnly()

    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 0, (
        f"x0 check failed: rs1 x{dut.rs1_idx_rf.value} expected 0, got {actual_rs1}"
    )
    assert actual_rs2 == 0, (
        f"x0 check failed: rs2 x{dut.rs2_idx_rf.value} expected 0, got {actual_rs2}"
    )
    
    # Reset Priority Check
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.rf_write_W.value = 1
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 20
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0
    dut.rs1_idx_rf.value = 7
    dut.rs2_idx_rf.value = 7
    
    await ReadOnly()
    
    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 20, (
        f"Reset-priority check failed: rs1 x{dut.rs1_idx_rf.value} expected 20, got {actual_rs1}"
    )
    assert actual_rs2 == 20, (
        f"Reset-priority check failed: rs2 x{dut.rs2_idx_rf.value} expected 20, got {actual_rs2}"
    )
    
    await Timer(100, unit="ps")
    
    dut.reset.value = 1
    dut.rf_write_W.value = 1
    dut.rs1_idx_rf.value = 7
    dut.rs2_idx_rf.value = 7
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 30
    
    await ReadOnly()
    
    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 30, (
        f"Reset-priority check failed: rs1 x{dut.rs1_idx_rf.value} expected 30, got {actual_rs1}"
    )
    assert actual_rs2 == 30, (
        f"Reset-priority check failed: rs2 x{dut.rs2_idx_rf.value} expected 30, got {actual_rs2}"
    )
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.reset.value = 1
    dut.rf_write_W.value = 0
    dut.rs1_idx_rf.value = 7
    dut.rs2_idx_rf.value = 7
    
    await ReadOnly()
    
    actual_rs1 = int(dut.rs1_val_D.value)
    actual_rs2 = int(dut.rs2_val_D.value)
    assert actual_rs1 == 0, (
        f"Reset-priority check failed: rs1 x{dut.rs1_idx_rf.value} expected 0, got {actual_rs1}"
    )
    assert actual_rs2 == 0, (
        f"Reset-priority check failed: rs2 x{dut.rs2_idx_rf.value} expected 0, got {actual_rs2}"
    )

    # Another Test with Reference Model
    model = RegFileModel()

    await FallingEdge(dut.clk)
    dut.reset.value = 1
    dut.rf_write_W.value = 0
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 100

    await RisingEdge(dut.clk)
    model.on_rising_edge(reset=True, we=0, rd=7, data=100)
    
    await FallingEdge(dut.clk)
    dut.reset.value = 0
    dut.rf_write_W.value = 1
    dut.rd_idx_W.value = 7
    dut.rs1_idx_rf.value = 7
    dut.WB_mux_result.value = 100
    
    await RisingEdge(dut.clk)
    model.on_rising_edge(reset=False, we=1, rd=7, data=100)
    
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0

    await ReadOnly()

    expected = model.read(rs=7, we=0, rd=7, data=100)
    actual = int(dut.rs1_val_D.value)
    assert actual == expected, (
        f"Reference model check: expected {expected}, got {actual}"
    )

    await FallingEdge(dut.clk)
    dut.rs1_idx_rf.value = 7
    dut.rf_write_W.value = 1
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 200

    await ReadOnly()
    
    expected = model.read(rs=7, we=1, rd=7, data=200)
    actual = int(dut.rs1_val_D.value)
    assert actual == expected, (
        f"Reference model check: expected {expected}, got {actual}"
    )

    await Timer(100, unit="ps")

    dut.rs1_idx_rf.value = 7
    dut.rf_write_W.value = 0
    dut.rd_idx_W.value = 7
    dut.WB_mux_result.value = 200

    await ReadOnly()

    expected = model.read(rs=7, we=0, rd=7, data=200) # we disable
    actual = int(dut.rs1_val_D.value)
    assert actual == expected, (
        f"Reference model check: expected {expected}, got {actual}"
    )

    # With Random Inputs - Uniform Random
    seed = int(os.getenv("RF_SEED", "2026")) # Env var
    rng = random.Random(seed)
    dut._log.info(f"Stimulus seed={seed}")

    for round in range(100):
        we = rng.randrange(2)
        rd = rng.randrange(32)
        rs1 = rng.randrange(32)
        rs2 = rng.randrange(32)
        data = rng.randrange(2**32)

        await FallingEdge(dut.clk)
        dut.reset.value = 0
        dut.rf_write_W.value = we
        dut.rd_idx_W.value = rd
        dut.rs1_idx_rf.value = rs1
        dut.rs2_idx_rf.value = rs2
        dut.WB_mux_result.value = data

        await ReadOnly()

        expected = model.read(rs=rs1, we=we, rd=rd, data=data)
        actual = int(dut.rs1_val_D.value)
        assert actual == expected, (
            f"seed={seed} cycle={round} port=rs1 rs={rs1} "
            f"we={we} rd={rd} data={data:#010x} "
            f"Random inputs test: expected={expected:#010x}, actual={actual:#010x}"
        )
        expected = model.read(rs=rs2, we=we, rd=rd, data=data)
        actual = int(dut.rs2_val_D.value)
        assert actual == expected, (
            f"seed={seed} cycle={round} port=rs2 rs={rs2} "
            f"we={we} rd={rd} data={data:#010x} "
            f"Random inputs test: expected={expected:#010x}, actual={actual:#010x}"
        )

        await RisingEdge(dut.clk)
        model.on_rising_edge(reset=False, we=we, rd=rd, data=data)
    
    ## Check regs values in the end
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0
    
    for idx in range(32):
        rs1 = idx
        rs2 = 31 - idx
        
        await FallingEdge(dut.clk)
        dut.rs1_idx_rf.value = rs1
        dut.rs2_idx_rf.value = rs2
        
        await ReadOnly()
        
        expected = model.read(rs=rs1, we=0, rd=0, data=0)
        actual = int(dut.rs1_val_D.value)
        assert actual == expected, (
            f"idx={idx}"
            f"Random inputs rs1 check: expected={expected:#010x}, actual={actual:#010x}"
        )
        expected = model.read(rs=rs2, we=0, rd=0, data=0)
        actual = int(dut.rs2_val_D.value)
        assert actual == expected, (
            f"idx={idx}"
            f"Random inputs rs2 check: expected={expected:#010x}, actual={actual:#010x}"
        )
        
    ## Biased random: Read-port Bypass
    mode_counts = [0, 0, 0, 0]

    for round in range(100):
        we = 1
        rd = rng.randrange(1, 32)
        data = rng.randrange(2**32)
        mode = rng.randrange(4)
        
        if mode == 0:
            rs1 = rng.randrange(32)
            rs2 = rng.randrange(32)
            mode_counts[mode] += 1
            if rs1 == rd:
                rs1 += rng.randint(1, 10)
            if rs2 == rd:
                rs2 += rng.randint(1, 10)
        elif mode == 1:
            rs1 = rd
            rs2 = rng.randrange(32)
            mode_counts[mode] += 1
            if rs2 == rd:
                rs2 += rng.randint(1, 10)
        elif mode == 2:
            rs1 = rng.randrange(32)
            rs2 = rd
            mode_counts[mode] += 1
            if rs1 == rd:
                rs1 += rng.randint(1, 10)
        elif mode == 3:
            rs1 = rd
            rs2 = rd
            mode_counts[mode] += 1
            
        await FallingEdge(dut.clk)
        dut.reset.value = 0
        dut.rf_write_W.value = 1
        dut.rd_idx_W.value = rd
        dut.rs1_idx_rf.value = rs1 & 0x1F
        dut.rs2_idx_rf.value = rs2 & 0x1F
        dut.WB_mux_result.value = data

        await ReadOnly()

        expected = model.read(rs=rs1 & 0x1F, we=we, rd=rd, data=data)
        actual = int(dut.rs1_val_D.value)
        assert actual == expected, (
            f"seed={seed} cycle={round} port=rs1 rs={rs1} "
            f"we={we} rd={rd} data={data:#010x} "
            f"Random inputs test: expected={expected:#010x}, actual={actual:#010x}"
        )
        expected = model.read(rs=rs2 & 0x1F, we=we, rd=rd, data=data)
        actual = int(dut.rs2_val_D.value)
        assert actual == expected, (
            f"seed={seed} cycle={round} port=rs2 rs={rs2} "
            f"we={we} rd={rd} data={data:#010x} "
            f"Random inputs test: expected={expected:#010x}, actual={actual:#010x}"
        )

        await RisingEdge(dut.clk)
        model.on_rising_edge(reset=False, we=we, rd=rd, data=data)
        
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0
    
    for idx in range(32):
        rs1 = idx
        rs2 = 31 - idx
        
        await FallingEdge(dut.clk)
        dut.rs1_idx_rf.value = rs1
        dut.rs2_idx_rf.value = rs2
        
        await ReadOnly()
        
        expected = model.read(rs=rs1, we=0, rd=0, data=0)
        actual = int(dut.rs1_val_D.value)
        assert actual == expected, (
            f"idx={idx}"
            f"Random inputs rs1 check: expected={expected:#010x}, actual={actual:#010x}"
        )
        expected = model.read(rs=rs2, we=0, rd=0, data=0)
        actual = int(dut.rs2_val_D.value)
        assert actual == expected, (
            f"idx={idx}"
            f"Random inputs rs2 check: expected={expected:#010x}, actual={actual:#010x}"
        )

    print(
        f"Two ports miss: {mode_counts[0]}",
        f"Only rs1 hits: {mode_counts[1]}",
        f"Only rs2 hits: {mode_counts[2]}",
        f"Two ports hit: {mode_counts[3]}",
        sep="\n",
        flush=True,
    )   

    dut._log.info("Reset and write checks passed")
