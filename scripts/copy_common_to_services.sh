#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

SERVICES=("monitor_service/app" "config_service/app" "alerter_service/app")

for service in ${SERVICES[@]}; do
    rm -rf "$SCRIPT_DIR/../$service/common/"
    cp -r "$SCRIPT_DIR/../common/" "$SCRIPT_DIR/../$service/"
done
