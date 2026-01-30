# collider
An experimental collision-detection library.

## Installation
The use of [miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommended to manage the dependencies. To install the dependencies, run the following command:
```bash
conda env create -f collider_env.yml
```
To activate the environment, run:
```bash
conda activate collider
```

This project uses [maturin](https://www.maturin.rs/) as the build system for the Rust and Python bindings. It can be installed directly using `pip`:
```bash
pip install maturin
```
To build the Rust code and install it directly as a Python package in the current `collider` virtual environment, run:
```bash
maturin develop --release -m collider-py/Cargo.toml
```
To run unit test of all crates, run:
```bash
cargo test
```