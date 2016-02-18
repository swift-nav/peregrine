#!/usr/bin/env bash

set -e

COMMON=test_data_common.sh

source aws_creds.sh
source $COMMON

# Create new tarball
rm -f $TEST_DATA_TAR
tar -czf $TEST_DATA_TAR test_data/

# Upload new tarball to S3
aws s3 cp $TEST_DATA_TAR s3://$TEST_DATA_URL_PATH

# Update tarball SHA
sed -i -e "s/\(TEST_DATA_SHA=\).*/\1$(shawesome $TEST_DATA_TAR)/g" $COMMON

# Commit new tarball SHA
git add $COMMON
git commit -m "Update tarball SHA"
