# RISC-V on Colorlight 5A-75B (v7.0)

Demonstration on using a Soft Core (**VexRiscv**)
built with **LiTex** in a **Colorlight 5A-7B** (ECP5).

### Current configuration
 * CPU runs at 198MHz with 32KB cache
 * 4MB SDRAM running at 66MHz
 * Gigabit ethernet PHY enabled with netboot support (not tested yet)
 * FPGA configuration is downloaded in RAM, no flash support yet

## Introduction

This demo is based on
[litexOnColorlightLab004](https://github.com/trabucayre/litexOnColorlightLab004)

- I removed the relocated serial port, so no hardware modifications are needed
- There is no LED and no User Button - both pins are used by the UART

| name      | Pin | note            |
|-----------|-----|-----------------|
| clk25     | P6  | 25MHz clock     |
| cpu_reset | --- | (deleted)       |
| user_led  | --- | (deleted)       |
| Uart TX   | U16 | J19 (DATA_LED-) |
| Uart RX   | R16 | J19 (KEY+)      |

### Required hardware

- **STM32 - blue pill** board repurposed as JTAG probe (see [dirtyJTAG](https://github.com/jeanthom/DirtyJTAG))
- **ColorLight** has no on-board JTAG adapter, so user must solder a pinheader
  (**J27** for JTAG signals, **J33** for VCC and **J34** for GND) and connect an external probe (see
  [chubby75](https://github.com/q3k/chubby75/tree/master/5a-75b))
- an USB <-> serial converter must be used to have access to serial interface

### Software setup

- [Detailed instructions on the setup for Ubuntu 20.04 are on my blog](https://blog.pcbxprt.com/index.php/2020/07/19/running-risc-v-core-on-small-fpga-board/)

## Build

### gateware (aka FPGA configuration)
Just:
```bash
./base.py --build
```
### firmware (code that runs on the RISC-V CPU after boot)
```bash
cd firmware && make
```
see [lab004] for more details.

## Load FPGA bitstream
```bash
./base.py --load --cable dirtyJtag
```

## Load and run RISC-V firmware
```bash
lxterm /dev/ttyUSBx --speed 38400 --kernel firmware/firmware.bin
```
where *ttyUSBx* is your USB <-> UART converter device. Sometimes it is called /dev/ttyACMx.

This command runs a special serial terminal which waits for a magic string, then uploads the binary firmware/firmware.bin to the FPGA and runs it.

*Note: The standard UART speed is 115200 bps, however because we are running the CPU at 3x the system clock the UART speed ends up being 115200/3 = 38400 bps*

## Boot screen
The following screen is captured with minicom. You can see the magic string output for the lxterm serial bootloader. The console is interactive, you can type 'help' for a list of commands.

```
        __   _ __      _  __
       / /  (_) /____ | |/_/
      / /__/ / __/ -_)>  <
     /____/_/\__/\__/_/|_|
   Build your hardware, easily!

 (c) Copyright 2012-2020 Enjoy-Digital
 (c) Copyright 2007-2015 M-Labs

 BIOS built on Jul 21 2020 03:27:32
 BIOS CRC passed (b5178a5a)

 Migen git sha1: 731c192
 LiteX git sha1: 63c19ff4

--=============== SoC ==================--
CPU:       VexRiscv @ 198MHz
BUS:       WISHBONE 32-bit @ 4GiB
CSR:       8-bit data
ROM:       32KiB
SRAM:      8KiB
L2:        32KiB
MAIN-RAM:  4096KiB

--========== Initialization ============--
Ethernet init...
Initializing DRAM @0x40000000...
SDRAM now under software control
SDRAM now under hardware control
Memtest at 0x40000000...
[########################################]
[########################################]
Memtest OK
Memspeed at 0x40000000...
Writes: 461 Mbps
Reads:  382 Mbps

--============== Boot ==================--
Booting from serial...
Press Q or ESC to abort boot completely.
sL5DdSMmkekro
Timeout
Booting from network...
Local IP : 192.168.1.50
Remote IP: 192.168.1.100
Booting from boot.json...
Booting from boot.bin...
Copying boot.bin to 0x40000000... 
Network boot failed.
No boot medium found

--============= Console ================--

litex> 

```