#!/usr/bin/env bash

export TEST_DATA_TAR=peregrine_ci_test_data.tar.gz
export TEST_DATA_SHA=fa939cd321dbe9b12b1f45ded90591cc7c23af1b
export TEST_DATA_URL_PATH=downloads.swiftnav.com/baseband_samples/$TEST_DATA_TAR
export TEST_DATA_URL=http://downloads.swiftnav.com.s3-us-west-1.amazonaws.com/baseband_samples/$TEST_DATA_TAR

# Remove filename from shasum
function shasum-abridged()
{
  echo "$(sum=($(shasum -a 1 $1)); echo $sum)"
}

