#!/usr/bin/env python

import setuptools

long_description = """
A Pure-Python library built as a PDF toolkit.  It is capable of:

- extracting document information (title, author, ...),
- splitting documents page by page,
- merging documents page by page,
- cropping pages,
- merging multiple pages into a single page,
- encrypting and decrypting PDF files.

By being Pure-Python, it should run on any Python platform without any
dependencies on external libraries.  It can also work entirely on StringIO
objects rather than file streams, allowing for PDF manipulation in memory.
It is therefore a useful tool for websites that manage or manipulate PDFs.
"""

setup_params = dict(
    name="PDF",
    use_hg_version=True,
    description="PDF toolkit",
    long_description=long_description,
    author="Mathieu Fenniak",
    author_email="biziqe@mathieu.fenniak.net",
    maintainer="Jason R. Coombs",
    maintainer_email="jaraco@jaraco.com",
    url="https://github.com/jaraco/PDF",
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    packages=["PDF"],
    setup_requires=['hgtools<4dev'],
    use_2to3=True,
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
