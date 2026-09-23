"""
The shared intermediate representation (IR) every PPM adapter produces, plus
a thin re-export of Confident/unwrap.

Confident/unwrap were promoted to workflow/common/ir.py on 2026-07-16 --
both were already fully generic (see that module's own docstring), and a
second component (Classify semantics, workflow/classify/) needed the
identical wrapper. REQUIRED_IR_KEYS and LANG_INCLUSION_KEYS stay here: they
describe Extract's own IR shape specifically (Classify semantics has its own,
different, IR shape -- see workflow/classify/mpi/classify_mpi.py etc.), not a
shared contract.

Only the 24 syntactic+derived fields from curated/field-provenance.json ever
flow through this IR -- see workflow/README.md
§5 for the interface contract this whole module exists to satisfy, and the
"Scope" section of the Extract design (this session's approved plan) for
the exact field list.

IR shape, one dict per function:

    {
        "model": "mpi",                 # required -- identity.model enum value
        "function_key": "mpi_bcast",     # required -- used to build "model:function_key"
        "name": "MPI_Bcast",             # required -> identity.name
        "type_family": [str, ...]|None,  # (opt) -> identity.type_family -- canonical typenames a
                                          # type-generic family's identity.name is generic over
                                          # (e.g. ["int","long","bfloat16",...] when "name" itself
                                          # contains a "{T}" placeholder, e.g. "nvshmem_{T}_put").
                                          # Resolved 2026-07-16: this is a purely mechanical, source-
                                          # derived signal for NVSHMEM/OpenSHMEM's type-generic macro/
                                          # table families (see workflow/extract/nvshmem/adapter.py,
                                          # workflow/extract/shmem/adapter.py), not semantic-tier --
                                          # see curated/field-provenance.json's updated entry.

        "desc": Confident|str|None,           # -> identity.desc
        "since": Confident|str|None,          # -> identity.since
        "deprecated_in": Confident|str|None,  # -> identity.deprecated_in
        "standard_refs": [str, ...],          # (opt, default []) -> identity.standard_refs

        "bindings": {                    # -> bindings.* -- each value None or a dict matching
                                          # $defs/binding_c, binding_fortran90, etc. exactly
            "c": {"expressible": bool, "header": str, "signature": str} | None,
            "fortran90": {"name": str, "expressible": bool, "use_colons": bool,
                           "index_overload": bool|None, "not_with_mpif": bool} | None,
            "fortran08": {"name": str, "expressible": bool,
                           "abstract_interface": bool, "module": str} | None,
            "lis": {"expressible": bool} | None,
            "cpp": {"expressible": bool, "class_method": str|None} | None,
        },

        "parameters": [
            {
                "name": str, "direction": "in"|"out"|"inout", "desc": str|None,
                "binding_type": {"c": str|None, "fortran90": str|None, "fortran08": str|None,
                                   "lis": str|None, "cpp": str|None},
                "asynchronous": bool, "constant": bool, "pointer": bool|None,
                "array_type": "fixed"|"variable"|"2d"|None, "func_type": str|None,
                "length": str|int|None, "root_only": bool,
                "_lang_included": {"c": bool, "c_large": bool, "fortran90": bool,
                                     "fortran90_optional": bool, "fortran08": bool,
                                     "fortran08_optional": bool, "lis": bool,
                                     "lis_large": bool, "cpp": bool},
            }, ...
        ],

        "return_kind": "ERROR_CODE"|"RESULT"|"void"|"bool"|"value",   # required
        "return_binding_type": {"c": str|None, ...},                   # (opt, default all-None)

        "flags": [Flag(...), ...],   # (opt) entry-scoped notes, folded into the run's report
    }
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.ir import Confident, unwrap  # noqa: F401,E402

REQUIRED_IR_KEYS = ("model", "function_key", "name", "return_kind")

LANG_INCLUSION_KEYS = (
    "c", "c_large",
    "fortran90", "fortran90_optional",
    "fortran08", "fortran08_optional",
    "lis", "lis_large",
    "cpp",
)
