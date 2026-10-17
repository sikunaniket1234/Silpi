# -*- coding: utf-8 -*-
"""Silpi launcher: start with pythonw for a windowless background app."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from silpi.app import main  # noqa: E402

if __name__ == "__main__":
    main()
