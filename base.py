#!/usr/bin/env python3

import os
import argparse
import sys

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
from litedram.phy import GENSDRPHY
from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII

# BaseSoC -----------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, with_usb_pll=False):
        self.clock_domains.cd_sys    = ClockDomain()
        self.clock_domains.cd_sys_ps = ClockDomain()

        # # #

        # Clk / Rst
        clk25 = platform.request("clk25")
        rst_n = 1

        # PLL
        self.submodules.pll = pll = ECP5PLL()

        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        pll.create_clkout(self.cd_sys_ps, sys_clk_freq, phase=180) # Idealy 90° but needs to be increased.
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll.locked | ~rst_n)

        # SDRAM clock
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), ClockSignal("sys_ps"))

class BaseSoC(SoCCore):
    def __init__(self, revision):
        platform = colorlight_5a_75b.Platform(revision)
        sys_clk_freq = int(50e6)

        # custom serial using j1 pins instead of led & button
        # platform.add_extension(_serial)

        # SoC with CPU
        SoCCore.__init__(self, platform,
            cpu_type                 = "vexriscv",
            clk_freq                 = sys_clk_freq*3,
            ident                    = "LiteX CPU Test SoC 5A-75B",
            ident_version            = True,
            integrated_rom_size      = 0x8000)

        # Clock Reset Generation
        # self.submodules.crg = CRG(platform.request("clk25"))

        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.submodules.sdrphy = GENSDRPHY(platform.request("sdram"))
        self.add_sdram("sdram",
            phy                     = self.sdrphy,
            module                  = M12L16161A(sys_clk_freq, "1:1"),
            origin                  = self.mem_map["main_ram"],
            size                    = 4*1024*1024,
            l2_cache_size           = 32768,
            l2_cache_min_data_width = 128,
            l2_cache_reverse        = True
        )
        self.submodules.ethphy = LiteEthPHYRGMII(
            clock_pads = self.platform.request("eth_clocks"),
            pads       = self.platform.request("eth"))
        self.add_csr("ethphy")
        self.add_ethernet(phy=self.ethphy)


# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Colorlight 5A-75B")
    builder_args(parser)
    soc_core_args(parser)
    trellis_args(parser)
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load",  action="store_true", help="Load bitstream")
    parser.add_argument("--cable", default="ft2232",    help="JTAG probe model")
    args = parser.parse_args()

    soc = BaseSoC(revision="7.0")

    builder = Builder(soc, **builder_argdict(args))
    builder.build(**trellis_argdict(args), run=args.build)

    if args.load:
        print(args.cable)
        os.system("openFPGALoader -c " + args.cable + " " + \
            os.path.join(builder.gateware_dir, soc.build_name + ".bit"))

if __name__ == "__main__":
    main()
