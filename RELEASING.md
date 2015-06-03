### Requirements

    $ pip install --upgrade pip
    $ pip install wheel
    $ pip install twine


### Making a release

To roll a release for this project, do the following:

    $ git tag 0.3.5   # no 'v' prefix or anything
    $ make release

This requires write access to both the GitHub repo, and to the PyPI package.
