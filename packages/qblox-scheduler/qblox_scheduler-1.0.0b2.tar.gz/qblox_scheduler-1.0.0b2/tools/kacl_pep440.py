# Repository: https://gitlab.com/qblox/packages/software/qblox-scheduler
# Licensed according to the LICENSE file on the main branch
"""
Script that monkey patches and launches the `kacl-cli` changelog linter
to make it compatible with the PEP440 versioning as well as semver.
"""

try:
    from kacl.kacl_cli import start
    from kacl.parser import KACLParser
except ImportError:
    raise ImportError(
        "Dev dependencies not installed.\nTo use this tool, please run: pip install -e .[dev]"
    ) from None

# fmt: off
if KACLParser.semver_regex == r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?":  # noqa: E501
    KACLParser.semver_regex = KACLParser.semver_regex.replace(r"(?:-", r"(?:-?")
# fmt: on
else:
    raise RuntimeError(
        "The semver validation regex included in this version of `python-kacl` does not match "
        "the expected value to be patched: this script must be modified."
    )

if __name__ == "__main__":
    start()
