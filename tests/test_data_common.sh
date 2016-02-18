#!/usr/bin/env bash

export TEST_DATA_TAR=peregrine_ci_test_data.tar.gz
export TEST_DATA_SHA=53b0fe1978ae7761e81cbbfc468ccd8758deebd5
export TEST_DATA_URL_PATH=downloads.swiftnav.com/baseband_samples
export TEST_DATA_URL=http://downloads.swiftnav.com.s3-us-west-1.amazonaws.com/baseband_samples/$TEST_DATA_TAR

# Remove filename from shasum
function shawesome()
{
  echo "$(sum=($(shasum -a 1 $1)); echo $sum)"
}

