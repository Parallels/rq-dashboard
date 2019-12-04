import os

from setuptools import find_packages, setup


def get_version():
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'rq_dashboard/version.py')) as f:
        locals = {}
        exec(f.read(), locals)
        return locals['VERSION']
    raise RuntimeError('No version info found.')


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='rq-dashboard',
    version=get_version(),
    url='https://github.com/Parallels/rq-dashboard',
    license='BSD',
    author='Vincent Driessen',
    author_email='vincent@3rdcloud.com',
    description='rq-dashboard is a general purpose, lightweight, web interface'
                ' to monitor your RQ queues, jobs, and workers in realtime.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=['rq>=1.0', 'Flask', 'redis', 'arrow', 'redis-sentinel-url'],
    entry_points={
        'console_scripts': [
            'rq-dashboard = rq_dashboard.cli:main'
        ]
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Monitoring',
    ]
)
