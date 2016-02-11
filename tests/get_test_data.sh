#!/usr/bin/env bash

TEST_DATA_URL=http://downloads.swiftnav.com.s3-us-west-1.amazonaws.com/baseband_samples/peregrine_ci_test_data.tar.gz

set -e

curl -O $TEST_DATA_URL
tar -xf peregrine_ci_test_data.tar.gz
