# -*- coding: utf-8 -*-
"""rslume setup script

:copyright: Copyright (c) 2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
import pykern.pksetup

pykern.pksetup.setup(
    name="rslume",
    author="RadiaSoft LLC",
    author_email="pip@radiasoft.net",
    description="RadiaSoft LUME wrappers",
    install_requires=[
        "pykern",
    ],
    license="http://www.apache.org/licenses/LICENSE-2.0.html",
    url="https://github.com/radiasoft/rslume",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],
)
