#!/bin/sh

set -v

closure_build_directory_component VAR_COMPONENT_DIR_PATH="${CUSTOM_ENV_PROJECT_DIRECTORY_PATH}" || exit

closure_clean_use_less_upload_directory
closure_upload_artifact

