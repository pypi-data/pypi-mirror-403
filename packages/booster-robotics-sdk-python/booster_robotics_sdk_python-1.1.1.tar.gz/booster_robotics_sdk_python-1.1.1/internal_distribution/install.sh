#!/bin/bash
script_path=$(readlink -f "$0")
root_path=$(dirname $script_path)

# 定义安装目录
INSTALL_PREFIX=${PREFIX:-/usr/local}
INCLUDE_DIR=$INSTALL_PREFIX/include

echo "Installing headers to $INCLUDE_DIR"

# 创建目标目录（如果不存在）
sudo mkdir -p $INCLUDE_DIR

# 递归安装头文件，保持目录结构
find $root_path/internal_include -name "*.h" -o -name "*.hpp" | while read file; do
    # 计算相对路径
    rel_path=${file#$root_path/internal_include/}
    target_dir=$INCLUDE_DIR/$(dirname $rel_path)
    
    # 创建目标目录
    sudo mkdir -p $target_dir
    
    # 安装文件，设置权限为644
    sudo install -m 644 $file $INCLUDE_DIR/$rel_path
    echo "Installed: $rel_path"
done

echo "Header installation completed"