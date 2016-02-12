****************************************
Updating test data
****************************************


Update the test data files with the following steps::

- Add new test data files to tests/test_data

- Create a new test data tarball

    $ tar -czf peregrine_ci_test_data.tar.gz test_data/

- Upload this tarball to downloads.swiftnav.com on Amazon S3.
  Please archive the old tarball before overwriting it.

    http://downloads.swiftnav.com.s3-us-west-1.amazonaws.com/baseband_samples/peregrine_ci_test_data.tar.gz

- Update the test data tarball SHA sum in `get_test_data.sh`

    $ sed -i -e "s/\(TEST_DATA_SHA=\).*/\1$(shasum -a 1 peregrine_ci_test_data.tar.gz | head -c 40)/g" get_test_data.sh

- Commit `get_test_data.sh` and push

    $ git add get_test_data.sh
    $ git commit -m "New test data"
    $ git push origin my_branch

