#!/bin/sh

set -v

closure_apt_get_remove_package VAR_PACKAGE_NAME="gcc"
closure_apt_get_remove_package VAR_PACKAGE_NAME="g++"
closure_apt_get_install_package VAR_PACKAGE_NAME="gcc-11"
closure_apt_get_install_package VAR_PACKAGE_NAME="g++-11"

closure_apt_get_install_package VAR_PACKAGE_NAME="libssl-dev"
closure_apt_get_install_package VAR_PACKAGE_NAME="libasio-dev"
closure_apt_get_install_package VAR_PACKAGE_NAME="libtinyxml2-dev"

. "${CUSTOM_ENV_PROJECT_DIRECTORY_PATH}"/shared-file-system/script/s-40-build-component.sh
