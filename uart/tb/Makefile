SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../rtl/baud_gen.sv
COCOTB_TOPLEVEL = baud_gen
COCOTB_TEST_MODULES = test_baud_gen

OVERSAMPLE ?= 1
COMPILE_ARGS += -g2012 -Pbaud_gen.oversample=$(OVERSAMPLE)
export OVERSAMPLE

include $(shell cocotb-config --makefiles)/Makefile.sim