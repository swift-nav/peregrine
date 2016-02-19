#!/usr/bin/env bash

export TEST_DATA_TAR=peregrine_ci_test_data.tar.gz
export TEST_DATA_SHA=260f5e3bc5d3c581b03a955547ad02c87d82efcd
export TEST_DATA_URL_PATH=downloads.swiftnav.com/baseband_samples/$TEST_DATA_TAR
export TEST_DATA_URL=http://downloads.swiftnav.com.s3-us-west-1.amazonaws.com/baseband_samples/$TEST_DATA_TAR

# Remove filename from shasum
function shasum-abridged()
{
  echo "$(sum=($(shasum -a 1 $1)); echo $sum)"
}

