#!/usr/bin/env python3

import os
import argparse
import sys
import subprocess

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.io import DDROutput
#from migen.genlib.io import CRG

#from litex.build.generic_platform import IOStandard, Subsignal, Pins
from litex_boards.platforms import colorlight_5a_75b

from litex.build.lattice.trellis import trellis_args, trellis_argdict

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litedram.modules import M12L16161A
from litedram.phy import HalfRateGENSDRPHY
from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII

kB = 1024
mB = 1024*kB

# BaseSoC -----------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, use_internal_osc=False, with_usb_pll=False, with_rst=True, sdram_rate="1:1"):
        self.rst = Signal()
        self.clock_domains.cd_sys    = ClockDomain()
        if sdram_rate == "1:2":
            self.clock_domains.cd_sys2x    = ClockDomain()
            self.clock_domains.cd_sys2x_ps = ClockDomain(reset_less=True)
        else:
            self.clock_domains.cd_sys_ps = ClockDomain(reset_less=True)

        # # #

        # Clk / Rst
        if not use_internal_osc:
            clk = platform.request("clk25")
            clk_freq = 25e6
        else:
            clk = Signal()
            div = 5
            self.specials += Instance("OSCG",
                                p_DIV = div,
                                o_OSC = clk)
            clk_freq = 310e6/div

        rst_n = 1 if not with_rst else platform.request("user_btn_n", 0)

        # PLL
        self.submodules.pll = pll = ECP5PLL()
        self.comb += pll.reset.eq(~rst_n | self.rst)
        pll.register_clkin(clk, clk_freq)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        if sdram_rate == "1:2":
            pll.create_clkout(self.cd_sys2x,    2*sys_clk_freq)
            pll.create_clkout(self.cd_sys2x_ps, 2*sys_clk_freq, phase=180) # Idealy 90° but needs to be increased.
        else:
           pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=180) # Idealy 90° but needs to be increased.

        # USB PLL
        if with_usb_pll:
            self.submodules.usb_pll = usb_pll = ECP5PLL()
            self.comb += usb_pll.reset.eq(~rst_n | self.rst)
            usb_pll.register_clkin(clk, clk_freq)
            self.clock_domains.cd_usb_12 = ClockDomain()
            self.clock_domains.cd_usb_48 = ClockDomain()
            usb_pll.create_clkout(self.cd_usb_12, 12e6, margin=0)
            usb_pll.create_clkout(self.cd_usb_48, 48e6, margin=0)

        # SDRAM clock
        sdram_clk = ClockSignal("sys2x_ps" if sdram_rate == "1:2" else "sys_ps")
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)

class BaseSoC(SoCCore):
    def __init__(self, revision):
        SoCCore.mem_map = {
            "rom":          0x00000000,
            "sram":         0x10000000,
            "spiflash":     0x20000000,
            "main_ram":     0x40000000,
            "csr":          0x82000000,
        }

        platform = colorlight_5a_75b.Platform(revision)
        sys_clk_freq = int(90e6)

        # SoC with CPU
        SoCCore.__init__(self, platform,
            cpu_type                 = "vexriscv",
            cpu_variant              = "linux",
            clk_freq                 = sys_clk_freq,
            ident                    = "LiteX RISC-V SoC on 5A-75B",
            ident_version            = True,
            max_sdram_size           = 0x200000, # Limit mapped SDRAM to 2MB.
            integrated_rom_size      = 0x8000)

        self.submodules.crg = _CRG(
            platform         = platform,
            sys_clk_freq     = sys_clk_freq,
            use_internal_osc = False,
            with_usb_pll     = True,
            with_rst         = False,
            sdram_rate       = "1:2")

        self.submodules.sdrphy = HalfRateGENSDRPHY(platform.request("sdram"))
        self.add_sdram("sdram",
            phy                     = self.sdrphy,
            module                  = M12L16161A(sys_clk_freq, "1:2"),
            origin                  = self.mem_map["main_ram"],
            size                    = 2*mB,
            l2_cache_size           = 0x8000,
            l2_cache_min_data_width = 128,
            l2_cache_reverse        = True
        )

        self.submodules.ethphy = LiteEthPHYRGMII(
            clock_pads = self.platform.request("eth_clocks", 0),
            pads       = self.platform.request("eth", 0),
            tx_delay   = 0e-9)
        self.add_csr("ethphy")
        self.add_ethernet(phy=self.ethphy)

        self.add_spi_flash(mode="1x", dummy_cycles=8)

    # DTS generation ---------------------------------------------------------------------------
    def generate_dts(self, board_name="colorlight_5a_75b"):
        json = os.path.join("build", board_name, "csr.json")
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        subprocess.check_call(
            "./json2dts.py {} > {}".format(json, dts), shell=True)

    # DTS compilation --------------------------------------------------------------------------
    def compile_dts(self, board_name="colorlight_5a_75b"):
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        dtb = os.path.join("buildroot", "rv32.dtb")
        subprocess.check_call(
            "dtc -O dtb -o {} {}".format(dtb, dts), shell=True)

    def configure_boot(self):
        if hasattr(self, "spiflash"):
            self.add_constant("FLASH_BOOT_ADDRESS", self.mem_map["spiflash"] + 1*mB)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Colorlight 5A-75B")
    builder_args(parser)
    soc_core_args(parser)
    trellis_args(parser)
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    parser.add_argument("--cable", default="dirtyJtag", help="JTAG probe model")
    args = parser.parse_args()

    soc = BaseSoC(revision="7.0")

    builder = Builder(
        soc,
        csr_json=os.path.join(os.path.join("build", "colorlight_5a_75b"), "csr.json"),
        bios_options=["TERM_MINI"])
    builder.build(**trellis_argdict(args), run=args.build)

    #soc.generate_dts()

    if args.load:
        print(args.cable)
        os.system("openFPGALoader -c " + args.cable + " " + \
            os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
