#!/bin/bash

# 获取当前脚本文件的绝对路径
script_path=$(readlink -f "$0")

# 提取根路径的父目录
root_path=$(dirname $script_path)

install_deps_script_path=$root_path/sdk_release/install.sh

sh $install_deps_script_path

echo "Install dependencies successfully!"