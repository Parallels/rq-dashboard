"""Common development operations."""

import os
import os.path

from fabric.api import abort, env, hide, lcd, local, quiet, settings, task


def _relative_to_fabfile(*path):
    return os.path.join(os.path.dirname(env.real_fabfile), *path)


@task
def todo(*args):
    """List the TODOs and FIXMEs in the code and documentation."""
    with lcd(_relative_to_fabfile()):
        local(
            'grin -e ".pyc,.pyo" "FIXME|TODO" *')
        local(
            'grind -0 \'*.feature\' | '
            'grin -I \'*.feature\' -0 -f - "FIXME|TODO"')


@task
def style():
    """Use flake8 to check Python style, PEP8, and McCabe complexity.

    See http://pypi.python.org/pypi/flake8/

    .. note::

        * Files with the following header are skipped::

            # flake8: noqa

        * Lines that end with a ``# NOQA`` comment will not issue a warning.

    """
    with lcd(_relative_to_fabfile('rq_dashboard')):
        local(
            'flake8 '
            '--exclude=".svn,CVS,.bzr,.hg,.git,__pycache__,._*" '
            '--max-complexity=9 .')


@task
def isort():
    """Use isort to automatically (re-)order the import statements on the top of files"""
    with lcd(_relative_to_fabfile()):
        local('isort **/*.py')


@task
def clean():
    """Remove all generated files (.pyc, .coverage, .egg, etc)."""
    with lcd(_relative_to_fabfile()):
        local('find -name "*.pyc" | xargs rm -f')
        local('find -name .coverage | xargs rm -f')
        local('find -name .DS_Store | xargs rm -f')  # Created by OSX
        local('find -name ._DS_Store | xargs rm -f') # Created by OSX
        local('find -name "._*.*" | xargs rm -f')    # E.g. created by Caret
        local('rm -f .coverage.*')
        local('rm -rf build')
        local('rm -rf dist')


def _latest_git_tag():
    return local('git tag | sort -nr | head -n1', capture=True)


def _git_head_sha():
    return local('git rev-parse HEAD', capture=True)


def _git_tag_sha():
    return local(
        'git tag | sort -nr | head -n1 | xargs git rev-parse', capture=True)


def _abort_if_tag_is_not_at_head():
    """Confirm committed to git with appropriate tags."""
    latest_tag = _latest_git_tag()
    head_sha = _git_head_sha()
    tag_sha = _git_tag_sha()
    print 'Latest git tag: {}'.format(latest_tag)
    if head_sha != tag_sha:
        abort('Latest git tag is not at HEAD!')


@task
def build():
    """Check Git, clean, test, and build sdist and wheel."""
    clean()
    style()
    # TODO tests()
    local('python setup.py sdist bdist_wheel')


@task
def upload(index_server='pypitest'):
    """Submit build package to index server as found in `~/.pypirc`.

    The default is to PyPI test. Typically `~/.pypirc` will contain:

        [distutils]
        index-servers=
            pypi
            pypitest

        [pypitest]
        repository = https://testpypi.python.org/pypi
        username = <username>
        password = <password>

        [pypi]
        repository = https://pypi.python.org/pypi
        username = <username>
        password = <password>

    """
    _abort_if_tag_is_not_at_head()
    with lcd(_relative_to_fabfile()):
        # TODO switch to twine once the following bug has been fixed:
        # https://bugs.launchpad.net/pkginfo/+bug/1437570
        local(
            'python setup.py sdist bdist_wheel upload '
            ' -r {} --show-response'.format(index_server)
        )
