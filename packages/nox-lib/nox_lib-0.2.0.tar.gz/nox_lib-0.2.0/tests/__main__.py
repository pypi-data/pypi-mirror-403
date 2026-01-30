# Copyright (c) 2025 Adam Karpierz
# SPDX-License-Identifier: Zlib

import unittest
import sys
import logging

from . import test_dir, top_dir

log = logging.getLogger(__name__)


def main(argv=sys.argv[1:]):
    print("Running tests\n", file=sys.stderr)
    tests = unittest.defaultTestLoader.discover(start_dir=test_dir,
                                                top_level_dir=top_dir)
    result = unittest.TextTestRunner(verbosity=1).run(tests)
    return 0 if result.wasSuccessful() else 1


if __name__.rpartition(".")[-1] == "__main__":
    # logging.basicConfig(level=logging.INFO)
    # logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())
