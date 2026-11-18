import cocotb
from cocotb.clock import Clock, Timer
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly

@cocotb.test()
async def test_reg_file(dut):
    MASK_01 = 0x01
    MASK_05 = 0x1F
    MASK_32 = 0xFFFF_FFFF


    dut.clk.value = 0 & MASK_01
    dut.reset.value = 1 & MASK_01
    dut.rf_write_W.value = 0 & MASK_01
    dut.rs1_idx_rf.value = 0 & MASK_05
    dut.rs2_idx_rf.value = 0 & MASK_05
    dut.rd_idx_W.value = 0 & MASK_05
    dut.WB_mux_result.value = 0 & MASK_32

    clock = Clock(dut.clk, 1, unit="ns")
    clock.start(start_high=False)

    await RisingEdge(dut.clk)

    # Initialization test
    for idx in range(1, 32):
        await FallingEdge(dut.clk)
        dut.reset.value = 0 & MASK_01
        dut.rf_write_W.value = 1 & MASK_01
        dut.rd_idx_W.value = idx
        dut.WB_mux_result.value = 0xFFFF_FFFF & MASK_32
        
        await RisingEdge(dut.clk)
        
        await FallingEdge(dut.clk)
        dut.rf_write_W.value = 0 & MASK_01
        dut.rs1_idx_rf.value = idx
        
        await ReadOnly()
        
        acutal_rs1 = int(dut.rs1_val_D.value)
        assert acutal_rs1 == 0xFFFF_FFFF, (
            f"Write failed: rs1 x{idx} expected 0xFFFF_FFFF, got {acutal_rs1}"
        )
        
    await FallingEdge(dut.clk)
    dut.reset.value = 1 & MASK_01
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.reset.value = 0 & MASK_01
    
    for idx in range(32):
        await FallingEdge(dut.clk)
        dut.rs1_idx_rf.value = idx
        dut.rs2_idx_rf.value = 31 - idx

        await ReadOnly()

        acutal_rs1 = int(dut.rs1_val_D.value)
        acutal_rs2 = int(dut.rs2_val_D.value)
        assert acutal_rs1 == 0, (
            f"Reset failed: rs1 x{idx} expected 0, got {acutal_rs1}"
        )
        assert acutal_rs2 == 0, (
            f"Reset failed: rs2 x{31 - idx} expected 0, got {acutal_rs2}"
        )

    # Synchronous Write
    await FallingEdge(dut.clk)
    dut.reset.value = 0 & MASK_01
    dut.rf_write_W.value = 1 & MASK_01
    dut.rd_idx_W.value = 2 & MASK_05
    dut.WB_mux_result.value = 100 & MASK_32

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0 & MASK_01
    dut.rs1_idx_rf.value = 2 & MASK_05

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    assert acutal_rs1 == 100, (
        f"Synchronous write failed: rs1 x{dut.rs1_idx_rf.value} expected 100, got {acutal_rs1}"
    )

    # Combinational Read
    await FallingEdge(dut.clk)
    dut.rd_idx_W.value = 3 & MASK_05
    dut.rf_write_W.value = 1 & MASK_01
    dut.WB_mux_result.value = 200 & MASK_32
    
    await RisingEdge(dut.clk)
    
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0 & MASK_01
    dut.rs1_idx_rf.value = 2 & MASK_05
    dut.rs2_idx_rf.value = 3 & MASK_05

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    acutal_rs2 = int(dut.rs2_val_D.value)
    assert acutal_rs1 == 100, (
        f"Combinational read failed: rs1 x{dut.rs1_idx_rf.value} expected 100, got {acutal_rs1}"
    )
    assert acutal_rs2 == 200, (
        f"Combinational read failed: rs2 x{dut.rs2_idx_rf.value} expected 200, got {acutal_rs2}"
    )
    
    await FallingEdge(dut.clk)
    dut.rs1_idx_rf.value = 3 & MASK_05
    dut.rs2_idx_rf.value = 2 & MASK_05

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    acutal_rs2 = int(dut.rs2_val_D.value)
    assert acutal_rs1 == 200, (
        f"Synchronous write failed: rs1 x{dut.rs1_idx_rf.value} expected 200, got {acutal_rs1}"
    )
    assert acutal_rs2 == 100, (
        f"Synchronous write failed: rs2 x{dut.rs2_idx_rf.value} expected 100, got {acutal_rs2}"
    )

    # Test Bypass
    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 1 & MASK_01
    dut.rd_idx_W.value = 7 & MASK_05
    dut.WB_mux_result.value = 20 & MASK_32

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rf_write_W.value = 0 & MASK_01 # When rf_write = 0, bypass will not activate
    dut.rs1_idx_rf.value = 7 & MASK_05
    dut.rs2_idx_rf.value = 7 & MASK_05
    dut.rd_idx_W.value = 7 & MASK_05
    dut.WB_mux_result.value = 30 & MASK_32

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    acutal_rs2 = int(dut.rs2_val_D.value)
    assert acutal_rs1 == 20, (
        f"Bypass-disable failed: rs1 x{dut.rs1_idx_rf.value} expected 20, got {acutal_rs1}"
    )
    assert acutal_rs2 == 20, (
        f"Bypass-disable failed: rs2 x{dut.rs2_idx_rf.value} expected 20, got {acutal_rs2}"
    )

    await Timer(100, unit="ps")

    dut.rf_write_W.value = 1 & MASK_01 # When rf_write = 1, bypass will activate
    dut.rs1_idx_rf.value = 7 & MASK_05
    dut.rs2_idx_rf.value = 7 & MASK_05
    dut.rd_idx_W.value = 7 & MASK_05
    dut.WB_mux_result.value = 30 & MASK_32

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    acutal_rs2 = int(dut.rs2_val_D.value)
    assert acutal_rs1 == 30, (
        f"Bypass failed: rs1 x{dut.rs1_idx_rf.value} expected 30, got {acutal_rs1}"
    )
    assert acutal_rs2 == 30, (
        f"Bypass failed: rs2 x{dut.rs2_idx_rf.value} expected 30, got {acutal_rs2}"
    )

    # x0 Priority Check
    await FallingEdge(dut.clk)
    dut.rd_idx_W.value = 0 & MASK_05
    dut.WB_mux_result.value = 50 & MASK_32

    await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)
    dut.rs1_idx_rf.value = 0 & MASK_05
    dut.rs2_idx_rf.value = 0 & MASK_05

    await ReadOnly()

    acutal_rs1 = int(dut.rs1_val_D.value)
    acutal_rs2 = int(dut.rs2_val_D.value)
    assert acutal_rs1 == 0, (
        f"x0 check failed: rs1 x{dut.rs1_idx_rf.value} expected 0, got {acutal_rs1}"
    )
    assert acutal_rs2 == 0, (
        f"x0 check failed: rs2 x{dut.rs2_idx_rf.value} expected 0, got {acutal_rs2}"
    )

    dut._log.info("Reset and write checks passed")
