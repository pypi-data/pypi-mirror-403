# LCM Message Definitions

This repository contains LCM message definitions for the Dimos project and tools to generate those language bindings.

It depends on our [LCM fork](https://github.com/dimensionalOS/lcm) for generation since we introduced some convinience changes to python message definitions.

lcmgen from our lcm fork is conviniently pulled and built by our `flake.nix`

## Generating Bindings

Run `generate.sh` to regenerate all bindings:

```sh
./generate.sh
```

This will:
1. Convert ROS messages to LCM definitions (from `sources/ros_msgs/` to `lcm_types/`)
2. Generate Python bindings (`generated/python_lcm_msgs/`)
3. Generate C++ bindings (`generated/cpp_lcm_msgs/`)
4. Generate C# bindings (`generated/cs_lcm_msgs/`)
5. Generate Java bindings (`generated/java_lcm_msgs/`)
6. Generate Typescript bindings (`generated/ts_lcm_msgs/`)

## Directory Structure

- `sources/` - Source ROS message definitions and conversion tools
- `lcm_types/` - Generated LCM message definitions
- `generated/` - Generated language bindings

## Python Package

This repo is also a Python package and you can install it via `pip install dimos-lcm`
It is not very useful standalone and is meant to be used in conjuction with actual [dimOS](https://github.com/dimensionalOS/dimos)
