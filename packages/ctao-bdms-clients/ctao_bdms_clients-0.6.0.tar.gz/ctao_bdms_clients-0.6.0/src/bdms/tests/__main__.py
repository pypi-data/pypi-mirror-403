"""Entry point for running bdms tests.

This module allows running the bdms test suite using pytest when executed as a script:
    python -m bdms.tests [pytest options]

This is needed as long as https://github.com/pytest-dev/pytest/issues/1596 is not resolved.
"""

import os
import sys

HERE = os.path.dirname(__file__)

if __name__ == "__main__":
    import pytest

    errcode = pytest.main([HERE] + sys.argv[1:])
    sys.exit(errcode)
