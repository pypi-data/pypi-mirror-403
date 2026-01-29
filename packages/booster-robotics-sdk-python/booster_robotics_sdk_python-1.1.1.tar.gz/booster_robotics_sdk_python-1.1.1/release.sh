#!/bin/bash

# 初始化参数
is_package_only=false

# 参数解析
while [[ $# -gt 0 ]]; do
    case "$1" in
        -package)
            is_package_only=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# 获取脚本所在绝对路径
script_path=$(readlink -f "$0")
root_path=$(dirname "$script_path")
build_path="$root_path/build"
release_path="$root_path/sdk_release"

echo "Root path: $root_path"
echo "Build path: $build_path"
echo "Release path: $release_path"

# 检查Ubuntu版本
ubuntu_version=$(lsb_release -rs)
if [[ ! "$ubuntu_version" =~ ^22\. ]]; then
    echo "Error: Requires Ubuntu 22.xx, current is $ubuntu_version"
    exit 1
fi

# 创建目录结构
mkdir -p "$build_path/x86" "$build_path/arm"
mkdir -p "$release_path/lib/x86_64" "$release_path/lib/aarch64" "$release_path/include"

if ! $is_package_only; then
    # 构建x86_64版本
    echo "========================================"
    echo "Building x86_64 version (ORIN=OFF)"
    echo "========================================"

    cd "$build_path/x86" || exit 1
    cmake ../.. -DORIN=OFF
    make -j$(nproc)

    # 构建ARM版本
    echo "========================================"
    echo "Building ARM version (ORIN=ON)"
    echo "========================================"

    cd "$build_path/arm" || exit 1
    cmake ../.. -DORIN=ON
    make -j$(nproc)
else
    echo "Package-only mode: skipping build process"
fi

# 复制x86库文件
x86_lib="$build_path/x86/libbooster_robotics_sdk.a"
if [ -f "$x86_lib" ]; then
    cp "$x86_lib" "$release_path/lib/x86_64/"
    echo "x86_64 library copied to $release_path/lib/x86_64/"
else
    echo "Error: x86_64 library not found at $x86_lib"
    exit 1
fi

# 复制ARM库文件
arm_lib="$build_path/arm/libbooster_robotics_sdk.a"
if [ -f "$arm_lib" ]; then
    cp "$arm_lib" "$release_path/lib/aarch64/"
    echo "ARM library copied to $release_path/lib/aarch64/"
else
    echo "Error: ARM library not found at $arm_lib"
    exit 1
fi

# 复制头文件
echo "========================================"
echo "Copying header files..."
echo "========================================"

include_src="$root_path/include"
include_dst="$release_path/include"

rsync -a --delete "$include_src/" "$include_dst/"
echo "Headers copied to $include_dst"

echo "========================================"
echo "Operation completed successfully!"
echo "Mode: $($is_package_only && echo "Package-only" || echo "Full build")"
echo "Build artifacts:"
echo "  x86_64: $release_path/lib/x86_64/libbooster_robotics_sdk.a"
echo "  ARM:    $release_path/lib/aarch64/libbooster_robotics_sdk.a"
echo "  Headers: $release_path/include/"
echo "========================================"

exit 0