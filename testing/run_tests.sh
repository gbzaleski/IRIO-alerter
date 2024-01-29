#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
now=`date +"%Y-%m-%d-%H-%M-%S"`
pytest $SCRIPT_DIR --html=$SCRIPT_DIR/reports/$now.html