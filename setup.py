#!/usr/bin/env python

import setuptools

with open('README.txt') as readme_stream:
    readme = readme_stream.read()

with open('CHANGES.txt') as changes_stream:
    changes = changes_stream.read()

setup_params = dict(
    name="PDF",
    use_hg_version=True,
    description="PDF toolkit",
    long_description=readme + '\n\n' + changes,
    author="Mathieu Fenniak",
    author_email="biziqe@mathieu.fenniak.net",
    maintainer="Jason R. Coombs",
    maintainer_email="jaraco@jaraco.com",
    url="https://github.com/jaraco/PDF",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    packages=["PDF"],
    setup_requires=['hgtools'],
    use_2to3=True,
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
