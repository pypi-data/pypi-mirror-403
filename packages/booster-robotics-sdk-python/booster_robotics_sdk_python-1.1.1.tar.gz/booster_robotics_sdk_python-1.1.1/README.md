# Booster Robotics SDK
Booster Robotics SDK aims to provide a simple and easy-to-use interface for developers to control the Booster Robotics products. 

## Prebuild environment
* OS  (Ubuntu 22.04 LTS)  
* CPU  (aarch64 and x86_64)   
* Compiler  (gcc version 11.4.0) 

## Installation
```bash
pip3 install pybind11
# pip3 install pybind11-stubgen
```

## Build examples
```bash
mkdir build
cd build
cmake ..
make
```

## Build python binding api and install
```bash
mkdir build
cd build
cmake .. -DBUILD_PYTHON_BINDING=on
make
sudo make install

if pybind11-stubgen cannot be found even after pip install, export PATH
```bash
export PATH=/home/[user name]/.local/bin:$PATH
```
