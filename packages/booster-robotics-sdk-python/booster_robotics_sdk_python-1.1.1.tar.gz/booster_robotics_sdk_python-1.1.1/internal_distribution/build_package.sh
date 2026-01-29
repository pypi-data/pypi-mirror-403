#!/bin/sh
# 获取当前脚本文件的绝对路径
script_path=$(readlink -f "$0")
echo "Script path: $script_path"


# 提取父目录路径作为根路径
root_path=$(dirname $(dirname $script_path))
echo "root_path: $root_path"

cd `dirname $0`
cd ..

git_commit_id=$(git rev-parse --short=6 HEAD)

package_dir="$root_path/internal_distribution/packages/internal_sdk_$git_commit_id"
if [ ! -d "$package_dir" ]; then
    mkdir -p "$package_dir"
fi


cp -r "$root_path/internal_include" "$package_dir"

chmod +x "$root_path/internal_distribution/install.sh"
cp "$root_path/internal_distribution/install.sh" "$package_dir"

echo "Copy success"

makeself "$package_dir" "$root_path/internal_distribution/packages/internal_sdk_$git_commit_id.run" "Booster Internal SDK Installer" "./install.sh"
echo "Installer generated."