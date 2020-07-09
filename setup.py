#! /usr/bin/env python

from setuptools import setup

setup(
    name="vmux",
    description="vim/neovim/kakoune session handler within tmux",
    long_description=open('README.md', 'rt').read().strip(),
    long_description_content_type='text/markdown',
    author="Jan Christoph Ebersbach", author_email='jceb@e-jc.de',
    url="https://github.com/jceb/vmux",
    license='GPLv3',
    packages=['vmux'],
    install_requires=[
        'pynvim>=0.3.2',
    ],
    setup_requires=['pytest-runner', 'setuptools_scm'],
    tests_require=['pytest'],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'vmux = vmux.__main__:main'
        ]
    },
    use_scm_version={
        "local_scheme": "no-local-version"
        },
    zip_safe=False,
)
