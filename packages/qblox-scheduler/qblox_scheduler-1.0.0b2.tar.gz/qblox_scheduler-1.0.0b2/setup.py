#!/usr/bin/env python

"""The setup script."""

import os

from setuptools import setup

install_requires = ["setuptools>=66.1"]


def get_version_and_cmdclass(pkg_path):
    """Load version.py module without importing the whole package.

    Template code from miniver
    """
    import os
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("version", os.path.join(pkg_path, "_version.py"))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.__version__, module.get_cmdclass(pkg_path)


version, cmdclass = get_version_and_cmdclass(os.path.join("src", "qblox_scheduler"))

setup(
    install_requires=install_requires,
    version=version,
    cmdclass=cmdclass,
)
