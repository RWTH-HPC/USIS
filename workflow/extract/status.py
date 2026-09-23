"""
Thin re-export shim. Flag/Report/SEVERITIES were promoted to
workflow/common/status.py on 2026-07-16 -- both were already fully PPM- and
stage-agnostic (see that module's own docstring), and a second component
(Classify semantics, workflow/classify/) needed the identical machinery.
Kept here, importable the same bare way (`from status import Flag`) this
package's adapters/emit.py/cli.py/test_emit.py already use, so none of them
need to change.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.status import Flag, Report, SEVERITIES  # noqa: F401,E402
