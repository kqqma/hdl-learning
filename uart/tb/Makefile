SIM ?= icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../rtl/baud_gen.sv $(PWD)/../rtl/uart_tx.sv

COCOTB_TOPLEVEL ?= baud_gen
COCOTB_TEST_MODULES ?= test_$(COCOTB_TOPLEVEL)

OVERSAMPLE ?= 1
export OVERSAMPLE
ifeq ($(COCOTB_TOPLEVEL),baud_gen)
COMPILE_ARGS += -Pbaud_gen.oversample=$(OVERSAMPLE)
endif

include $(shell cocotb-config --makefiles)/Makefile.sim