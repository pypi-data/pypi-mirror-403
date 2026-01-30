#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

#${SCRIPT_DIR}/../../../run_test.sh -i /Configuration -t execute_persisted_post_processes
python3 "${SCRIPT_DIR}"/execute_persisted_post_processes.py
