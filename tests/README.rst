****************************************
Updating test data
****************************************

To update the test data tarball and upload to AWS S3
(requires AWS Command Line Interface):

- Add new test data files to `test_data/`.

- Ensure AWS credentials are filled out in `aws_creds.sh`.
  If not, ask an AWS knowledgable team member for help.

- Run `update_test_data.sh`. This will commit a new
  SHA in `test_data_common.sh`.

    $ ./update_test_data.sh

- Test it.

    $ ./get_test_data.sh
    $ py.test ./

- Create a Pull Request ASAP so test data is not
  out of date for Travis or other developers.

