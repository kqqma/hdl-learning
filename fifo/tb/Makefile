SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../rtl/fifo.sv

COCOTB_TOPLEVEL ?= fifo
COCOTB_TEST_MODULES ?= test_$(COCOTB_TOPLEVEL)

DEPTH ?= 4
export DEPTH
COMPILE_ARGS += -P$(COCOTB_TOPLEVEL).DEPTH=$(DEPTH)

include $(shell cocotb-config --makefiles)/Makefile.sim