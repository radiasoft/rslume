# -*- coding: utf-8 -*-
"""lume-rselegant setup script

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
import pykern.pksetup

pykern.pksetup.setup(
    name="lume-rselegant",
    author="RadiaSoft LLC",
    author_email="pip@radiasoft.net",
    description="elegant tools for use in LUME",
    install_requires=[
        "pykern",
        "sirepo",
    ],
    license="http://www.apache.org/licenses/LICENSE-2.0.html",
    url="https://github.com/radiasoft/lume-rselegant",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],
)
