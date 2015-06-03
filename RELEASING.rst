Requirements
============

::

    $ pip install -r requirements.txt


Making a release
================


Use the Fabric tasks. For example, to tag, build and upload to testpypi

::

    $ git tag 0.3.5   # no 'v' prefix or anything
    $ fab build
    $ fab upload

This requires write access to both the GitHub repo, and to the PyPI test site.

See `fab -l` for more options.
