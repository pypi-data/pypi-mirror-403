# `dotbot-provision`

A command-line tool for provisioning DotBot devices and gateways.

It can fetch, config, and flash pre-built firmwares from repos [SwarmIT](https://github.com/DotBots/swarmit) and [mari](https://github.com/DotBots/mari).

## Requirements

This tool shells out to external flashing utilities:

- `nrfjprog` (Nordic nRF Command Line Tools) for nRF5340 flashing
- `pyocd` for DAPLink/J-Link OB programmer flashing
- `JLinkExe` (SEGGER J-Link) for STM32 bootloader flashing

Make sure these are installed and available on your `PATH`.

## Installation

```bash
pip install dotbot-provision
```

```
Usage: dotbot-provision [OPTIONS] COMMAND [ARGS]...

  A tool for provisioning DotBot devices and gateways.

Options:
  --help  Show this message and exit.

Commands:
  fetch          Fetch firmware assets into bin/<fw-version>/.
  flash          Flash firmware + config using versioned bin layout.
  flash-bringup  Flash J-Link OB or DAPLink programmer firmware.
  flash-hex      Flash explicit app/net hex files.
  read-config    Read config from the device.
```

## Deploying a testbed

First, download firmware assets:

```bash
dotbot-provision fetch --fw-version v0.7.0
```

Then, to flash a DotBot-v3 while specifying a certain Network ID:

```bash
dotbot-provision flash --device dotbot-v3 --fw-version v0.7.0 --network-id 0100
```

You can also pass `-a <fw-name>` to flash, in addition to bootloader and netcore, a default app firmware:


```bash
dotbot-provision flash --device dotbot-v3 --fw-version v0.7.0 --network-id 0100 -a motors
```


And to flash a Mari Gateway:

```bash
dotbot-provision flash --device gateway --fw-version v0.7.0 --network-id 0100
```

... and it's done!

## Deploying a testbed on fresh robots

If your robot just arrived from factory, first you have to run the `flash-bringup` command.
You can concatenate it with a regular `flash` command so that all happens in sequence with minimal manual work.
Like this:

```bash
dotbot-provision flash-bringup --programmer-firmware jlink -d ../../../programer-files-dotbot && \
  dotbot-provision flash -d dotbot-v3 -f local -n 0100 -s 77
```
... where the `-s` flag stands for `--sn-starting-digits` and serves as a pattern to identify the connected programming probe. In this case it solves a problem where the flash command incorrectly selects the external J-Link probe instead of the dotbot's (most DotBots come from factory with a serial number starting by 77).
