SIM = verilator
TOPLEVEL_LANG = verilog

REPO_ROOT := $(abspath ../../..)

VERILOG_SOURCES = $(REPO_ROOT)/rtl/core/core_types_pkg.sv \
                  $(REPO_ROOT)/rtl/core/datapath/reg_file.sv
COCOTB_TOPLEVEL = reg_file
COCOTB_TEST_MODULES = test_reg_file

SIM_BUILD = $(REPO_ROOT)/sim/build/cocotb_reg_file
COCOTB_RESULTS_FILE = $(SIM_BUILD)/results.xml

include $(shell cocotb-config --makefiles)/Makefile.sim