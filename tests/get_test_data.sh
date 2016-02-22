#!/usr/bin/env bash

set -e

source test_data_common.sh

# Archive old data, fail silently if it doesn't exist
mv test_data test_data_old_$(date +%Y-%m-%d:%H:%M:%S) 2>/dev/null || true
rm -f $TEST_DATA_TAR

curl -O $TEST_DATA_URL

# Extract tarball if SHA checks out
if [ $(shasum-abridged $TEST_DATA_TAR) != $TEST_DATA_SHA ]; then
  echo "Error: test data has unknown SHA"
  exit 1
else
  tar -xf $TEST_DATA_TAR
fi

