# RISC-V on Colorlight 5A-75B (v7.0)

Demonstration on using a Soft Core (**VexRiscv**)
built with **LiTex** in a **Colorlight 5A-7B** (ECP5).

### Current configuration
 * CPU runs at 198MHz with 32KB cache
 * 4MB SDRAM running at 66MHz
 * Gigabit ethernet PHY enabled with netboot support (not tested yet)
 * FPGA configuration is downloaded in RAM, no flash support yet
### Introduction

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

### software

- [Detailed instructions on the setup for Ubuntu 20.04 are on my blog](https://blog.pcbxprt.com/index.php/2020/07/19/running-risc-v-core-on-small-fpga-board/)

### hardware

- **ColorLight** has no on-board JTAG adapter, so user must solder a pinheader
  (**J27** for JTAG signals, **J33** for VCC and **J34** for GND) and connect an external probe (see.
  [chubby75](https://github.com/q3k/chubby75/tree/master/5a-75b));
- an USB <-> serial converter must be used to have access to serial interface

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

## load bitstream
```bash
./base.py --load --cable dirtyJtag
```

## load firmware
```bash
lxterm /dev/ttyUSBx --kernel firmware/firmware.bin
```
where *ttyUSBx* is your USB <-> UART converter device. Sometimes it is called /dev/ttyACMx.

This code runs a special serial terminal which waits for a magic string, then uploads the binary firmware/firmware.bin to the FPGA and runs it.

