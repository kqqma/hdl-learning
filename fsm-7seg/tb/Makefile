SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# which module to test (default: sevenseg)
COCOTB_TOPLEVEL ?= sevenseg
COCOTB_TEST_MODULES ?= test_$(COCOTB_TOPLEVEL)
VERILOG_SOURCES = $(PWD)/../rtl/$(COCOTB_TOPLEVEL).v
# separate build folder per module, so they don't overwrite each other
SIM_BUILD = sim_build_$(COCOTB_TOPLEVEL)

include $(shell cocotb-config --makefiles)/Makefile.sim