#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd ${SCRIPT_DIR}/tests/behave/test_holado

#env HOLADO_STEPS_CATALOG=True behave --format steps.catalog --dry-run --no-summary -q
#env HOLADO_STEPS_CATALOG=True behave --format steps --dry-run --no-summary -q
env HOLADO_STEPS_CATALOG=True behave --format steps.doc --dry-run --no-summary -q | grep "^@"

