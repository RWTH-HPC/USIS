"""
Generate Formal's assignment half -- the previously-unbuilt component that
decides, for a given classified entry, which shapes.json shape_ref (if any)
applies and what its bindings should be (docs/workflow/
docs/schema/shape-catalog.md).

Runs against the full corpus (instances/1_syntactic-semantics-api.json,
~980 families). Every proposal is computed per entry, independently of the
rest of the corpus.

Every proposal this produces is `needs_approval`, full stop -- per the
2026-07-16 decision: there is no confidence score, no auto-ship threshold. This
script's output (curated/formal-assignments.json) is a proposals
file, structurally closer to curated/shapes/seed-assignments.json than to a shipped entry --
it is never merged into an entry automatically, and nothing downstream
treats it as final until a human promotes specific proposals.

Assignment strategy, in priority order:
  1. Exact (ppm, function) match against curated/shapes/seed-assignments.json -- reuse
     the already-authored, already-reviewed binding instead of re-deriving
     one from scratch. Still needs_approval (this script doesn't know the
     golden example was written for validation purposes rather than as a
     blanket assignment for every future entry naming that function), but
     the rationale says so plainly.
  2. `identity.api_group` in {query, management} -- propose
     "no_formal_applicable": matches the established convention that
     query/management calls carry no semantics.formal at all (an explicit
     non-goal, not a gap -- see
     docs/cross-ppm-analysis/known-gaps-and-open-questions.md, Non-goals).
  3. A small set of name-based rules for cases api_group heuristics don't
     cover cleanly (mpi_comm_rank/size, *_wait_until, *_fence/*_quiet).
     mpi_init/mpi_finalize/shmem_init/shmem_finalize used to need a rule
     here too, but as of 2026-07-17 Heuristic Classification tags all four
     "management" directly, so they're covered by step 2 above -- see
     propose_for_entry's inline comment at the api_group check.
  4. Category rules keyed on identity.api_group + the multiset of
     parameters[].kind already populated by Heuristic Classification
     (BUFFER/RANK/OPERATION/REQUEST) -- see _propose_collective/
     _propose_point_to_point/_propose_one_sided below for the concrete
     per-category logic and what each one is actually checking for.
  5. If nothing above fires: outcome "escalate_new_shape" -- per the
     resolved 2026-07-16 workflow rule (CLAUDE.md), "no shape fits" always
     escalates to Author Shapes to mint a new shape; this script never
     improvises an inline `formal` block and never forces a near-miss shape
     just because it's the closest one available.

Every "shape_assigned" proposal is additionally run through the existing,
already-tested expand.py + validate.py to attach a real expansion (or the
reason expansion/validation failed) -- so a human reviewing the proposals
file sees the actual would-be semantics.formal block, not just a shape name
and a guess at its bindings.
"""

import hashlib
import json
import os
import re
import sys
import datetime

_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)

from expand import expand_entry  # noqa: E402
from validate import validate_formal, ValidationError as FormalValidationError  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import CURATED_DIR, OUT_DIR, REVIEW_DIR, SHAPES_DIR  # noqa: E402

sys.path.insert(0, os.path.join(_LAYOUT_COMMON, "..", "review"))
from record import BOILERPLATE, merge_and_write  # noqa: E402

_ROOT = os.path.join(_HERE, "..", "..")
_SHAPES_PATH = os.path.join(SHAPES_DIR, "shapes.json")
_SEED_PATH = os.path.join(SHAPES_DIR, "seed-assignments.json")
_SEMANTICS_API_PATH = os.path.join(OUT_DIR, "1_syntactic-semantics-api.json")
# Curated, not build output: these proposals are read and corrected by hand,
# and those corrections are what ships -- see curated/README.md.
_OUT_PATH = os.path.join(CURATED_DIR, "formal-assignments.json")
_REVIEW_PATH = os.path.join(REVIEW_DIR, "formal-assignments.review.json")

_KNOWN_GAPS_REF = "docs/cross-ppm-analysis/known-gaps-and-open-questions.md"

_TYPE_TOKENS = frozenset({
    "char", "short", "int", "long", "longlong", "ptrdiff", "size", "schar", "uchar", "ushort", "uint",
    "ulong", "ulonglong", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64",
    "float", "double", "longdouble", "complexf", "complexd", "half", "bfloat16",
})
_REDUCE_OP_WORDS = frozenset({"sum", "max", "min", "prod", "and", "or", "xor"})


# --- small parameter-inspection helpers, all grounded directly in fields
# Heuristic Classification already populated (parameters[].kind), never a
# fresh guess of this script's own -----------------------------------------

def _by_kind(params, kind):
    return [p for p in params if p.get("kind") == kind]


def _param_ref(name):
    return f"param:{name}"


def _name_tokens(function_key):
    return function_key.split("_")


# OpenSHMEM's fixed-size active-set collectives encode their element WIDTH,
# not an element type, as a trailing 32/64 on the operation word:
# shmem_broadcast32/64, shmem_collect32/64, shmem_fcollect32/64,
# shmem_alltoall32/64, shmem_alltoalls32/64 (all 10 confirmed present in the
# corpus). Their count parameter counts elements of that width, so defaulting
# them to 'type:byte' -- as the no-token fallback did until 2026-07-21 --
# understated every one of their extents by a factor of 4 or 8.
#
# The emitted token follows the existing 'type:byte' precedent: a size unit
# rather than a C type. 'bits32'/'bits64' is deliberately not spelled
# 'uint32'/'uint64', because these routines are untyped -- the standard
# describes them as moving 32/64 bits of data, and claiming a signedness the
# API does not have would be a wrong fit rather than a missing one.
_WIDTH_SUFFIX_TOKENS = {"32": "bits32", "64": "bits64"}


def _infer_type_token(function_key):
    for tok in _name_tokens(function_key):
        if tok.lower() in _TYPE_TOKENS:
            return tok.lower()
    for tok in _name_tokens(function_key):
        for suffix, token in _WIDTH_SUFFIX_TOKENS.items():
            # Only a *trailing* width on an otherwise-alphabetic operation word
            # ("broadcast32"), never a bare numeric token and never a token that
            # is already a recognized type name (int32/uint64 are handled above).
            if tok.lower().endswith(suffix) and tok[:-len(suffix)].isalpha():
                return token
    return None


def _name_reduce_op(function_key):
    for tok in _name_tokens(function_key):
        if tok.lower() in _REDUCE_OP_WORDS:
            return tok.lower()
    return None


def _count_param_name(params):
    c = _by_kind(params, "COUNT")
    return c[0]["name"].lower() if c else None


def _asymmetric_count(params):
    """True when the sole COUNT-kind parameter is itself send/recv-prefixed
    (e.g. NCCL's ncclReduceScatter/ncclAllGather 'recvcount'/'sendcount'),
    as opposed to a single symmetric 'count'/'nreduce' governing the whole
    buffer on every side (mpi_allreduce, ncclAllReduce, nvshmem_int_*_reduce).
    This is the signal that distinguishes the two already-logged-as-unbuilt
    shapes (gather_to_all, reduce_scatter) from the built uniform-extent
    ones -- forcing either into collective.all_to_all_reduce/
    one_to_all_uniform would silently drop the fact that each participant's
    extent actually differs."""
    n = _count_param_name(params)
    return n is not None and ("send" in n or "recv" in n)


def _scope_param_ref(params):
    for kind in ("COMMUNICATOR", "TEAM"):
        p = next(iter(_by_kind(params, kind)), None)
        if p:
            return _param_ref(p["name"])
    return None


def _prefixed_extent(params, prefixes):
    """Extent {count_ref, datatype_ref} preferring send/recv-prefixed COUNT and
    DATATYPE params (falling back to the first of each kind -- NCCL declares a
    single shared 'datatype'/'sendcount' where MPI declares independent
    send/recv pairs). Returns (extent_or_None, note_or_None); when no DATATYPE
    parameter exists at all, returns None with a note instead of inventing a
    'type:' token -- an offset expression built on a non-param datatype ref
    would violate the reference grammar (the known typed-API literal-token
    gap), so the binding is left for human completion rather than force-fit."""
    counts = _by_kind(params, "COUNT")
    dtypes = _by_kind(params, "DATATYPE")
    count = next((c for c in counts if any(h in c["name"].lower() for h in prefixes)), counts[0] if counts else None)
    dtype = next((d for d in dtypes if any(h in d["name"].lower() for h in prefixes)), dtypes[0] if dtypes else None)
    if count is None or dtype is None:
        missing = "COUNT" if count is None else "DATATYPE"
        return None, (f"no {missing}-kind parameter available for the "
                      f"{'/'.join(prefixes)}-side extent -- needs human completion")
    return {"count_ref": _param_ref(count["name"]), "datatype_ref": _param_ref(dtype["name"])}, None


def _extent_binding(params, function_key, type_family=None):
    count = _by_kind(params, "COUNT")
    if not count:
        return None, "no COUNT-kind parameter found for the extent slot"
    count_ref = _param_ref(count[0]["name"])
    dtype = _by_kind(params, "DATATYPE")
    if dtype:
        return {"count_ref": count_ref, "datatype_ref": _param_ref(dtype[0]["name"])}, None
    if type_family:
        # Collapsed type-generic family (identity.type_family populated) --
        # deterministic, not a name-inference guess: {T} is resolved to a
        # concrete type only by the Concretize workflow step, once per
        # chosen instantiation, never here. See docs/schema/schema-overview.md's
        # Type-genericity note and workflow/concretize/.
        return {"count_ref": count_ref, "datatype_ref": "type:{T}"}, None
    token = _infer_type_token(function_key)
    if token:
        return (
            {"count_ref": count_ref, "datatype_ref": f"type:{token}"},
            f"no runtime DATATYPE parameter -- inferred fixed element type '{token}' from the function "
            f"name itself, matching the 'type:<x>' convention already used in nvshmem_int_sum_reduce's "
            f"golden example ('type:int'); confirm this is the intended element type",
        )
    return (
        {"count_ref": count_ref, "datatype_ref": "type:byte"},
        "no runtime DATATYPE parameter and no type token recognizable in the function name -- defaulted "
        "to 'type:byte' (the untyped/mem-variant convention); confirm",
    )


def _pick_source_dest_buffers(params):
    buf = _by_kind(params, "BUFFER")
    if not buf:
        return None, None, "no BUFFER-kind parameters found"
    if len(buf) == 1:
        ref = _param_ref(buf[0]["name"])
        return ref, ref, None  # in-place style, e.g. mpi_bcast's single 'buffer' param
    source_hints = ("source", "src", "sendbuf", "sendbuff")
    dest_hints = ("dest", "recvbuf", "recvbuff")
    source = next((p for p in buf if any(h in p["name"].lower() for h in source_hints)), None)
    dest = next((p for p in buf if any(h in p["name"].lower() for h in dest_hints)), None)
    if source and dest:
        return _param_ref(source["name"]), _param_ref(dest["name"]), None
    in_p = next((p for p in buf if p.get("direction") == "in"), None)
    out_p = next((p for p in buf if p.get("direction") == "out"), None)
    if in_p and out_p:
        return _param_ref(in_p["name"]), _param_ref(out_p["name"]), None
    return None, None, f"could not disambiguate source/dest among BUFFER params {[p['name'] for p in buf]}"


def _root_selector(params):
    rank = _by_kind(params, "RANK")
    root = next((p for p in rank if "root" in p["name"].lower()), None)
    if root is None and len(rank) == 1:
        root = rank[0]
    if root is None:
        return None, "no RANK-kind parameter identifiable as the root"
    return f"rank == param:{root['name']}", None


def _target_selector(params):
    rank = _by_kind(params, "RANK")
    if len(rank) == 1:
        return f"rank == param:{rank[0]['name']}", None
    return None, f"could not identify a single RANK-kind target parameter (found {len(rank)})"


def _scope_selector(params):
    for kind in ("COMMUNICATOR", "TEAM"):
        p = next(iter(_by_kind(params, kind)), None)
        if p:
            return f"rank in param:{p['name']}", None
    return (
        "rank in all_pes",
        "no COMMUNICATOR/TEAM-kind parameter found -- defaulted to the whole-run scope selector "
        "using the 'all_pes' grammar token (added 2026-07-17 to docs/schema/reference-grammar.md "
        "specifically for this case; not a from-scratch invention)",
    )


# --- proposal constructors --------------------------------------------------

def _shape_proposal(entry_key, shape_ref, bindings, rationale, notes=None, extra=None):
    return {
        "entry_key": entry_key,
        "outcome": "shape_assigned",
        "shape_ref": shape_ref,
        "bindings": bindings,
        "extra": extra,
        "confidence": "needs_approval",
        "rationale": rationale,
        "binder_notes": [n for n in (notes or []) if n],
    }


def _no_formal_proposal(entry_key, rationale):
    return {
        "entry_key": entry_key,
        "outcome": "no_formal_applicable",
        "shape_ref": None,
        "bindings": None,
        "extra": None,
        "confidence": "needs_approval",
        "rationale": rationale,
        "binder_notes": [],
    }


def _escalate_proposal(entry_key, closest_shape_ref, rationale):
    return {
        "entry_key": entry_key,
        "outcome": "escalate_new_shape",
        "shape_ref": closest_shape_ref,
        "bindings": None,
        "extra": None,
        "confidence": "needs_approval",
        "rationale": rationale,
        "binder_notes": [],
    }


def _proposal_from_golden(entry_key, golden):
    return {
        "entry_key": entry_key,
        "outcome": "shape_assigned",
        "shape_ref": golden["shape_ref"],
        "bindings": golden["bindings"],
        # Found missing 2026-07-17 while authoring the p2p.direct_send/recv shapes: this
        # function used to drop golden["extra"] on the floor entirely, so even an exact
        # golden-example match (e.g. mpi_isend/mpi_irecv, both of which need extra to carry
        # their real sync.matching) silently expanded with matching=null. Fixed here rather
        # than left as a second undiscovered gap alongside the one this session set out to fix.
        "extra": golden.get("extra"),
        "confidence": "needs_approval",
        "rationale": (
            "matches a checked-in seed assignment for this exact function "
            "(curated/shapes/seed-assignments.json) -- one of the assignments this matcher's own "
            "rules cannot derive, so the binding is read from the seed rather than inferred. Still "
            "requires human confirmation like every Assignment proposal, but is not a from-scratch "
            "heuristic guess. Correct such an entry IN THE SEED: this file is rebuilt wholesale by "
            "--regenerate formal, the seed is not"
        ),
        "binder_notes": [],
    }


# --- category dispatch ------------------------------------------------------

def _propose_collective(entry_key, params, function_key, type_family=None):
    buf = _by_kind(params, "BUFFER")
    rank = _by_kind(params, "RANK")
    op = _by_kind(params, "OPERATION")
    name_op = _name_reduce_op(function_key)
    asymmetric = _asymmetric_count(params)

    if not buf and not rank and not op and not name_op:
        scope_sel, scope_note = _scope_selector(params)
        return _shape_proposal(
            entry_key, "sync_only.rendezvous", {"scope_selector": scope_sel},
            "collective with no BUFFER/RANK/OPERATION parameters at all -- pure synchronization "
            "barrier pattern, no data movement to describe",
            [scope_note],
        )

    if (op or name_op) and not rank and not asymmetric:
        source, dest, buf_err = _pick_source_dest_buffers(params)
        extent, extent_note = _extent_binding(params, function_key, type_family)
        scope_sel, scope_note = _scope_selector(params)
        if op:
            op_ref, op_note = f"param:{op[0]['name']}", None
        else:
            op_ref, op_note = (
                f"literal:{name_op}",
                f"no runtime OPERATION parameter -- operation '{name_op}' is fixed by the function name "
                f"itself, matching the 'literal:<op>' convention already used in nvshmem_int_sum_reduce's "
                f"golden example",
            )
        bindings = {"source_buffer": source, "dest_buffer": dest, "extent": extent,
                    "operation": op_ref, "scope_selector": scope_sel}
        return _shape_proposal(
            entry_key, "collective.all_to_all_reduce", bindings,
            "has an OPERATION-kind parameter or a name-fixed reduction operator, no root/RANK parameter, "
            "and a symmetric (non send/recv-prefixed) COUNT parameter -- every participant receives the "
            "full reduced result (allreduce-shaped)",
            [buf_err, extent_note, op_note, scope_note],
        )

    if op and rank and not asymmetric:
        source, dest, buf_err = _pick_source_dest_buffers(params)
        extent, extent_note = _extent_binding(params, function_key, type_family)
        root_sel, root_note = _root_selector(params)
        scope_sel, scope_note = _scope_selector(params)
        bindings = {"source_buffer": source, "dest_buffer": dest, "extent": extent, "operation": f"param:{op[0]['name']}",
                    "root_selector": root_sel, "scope_selector": scope_sel}
        return _shape_proposal(
            entry_key, "collective.all_to_one_reduce", bindings,
            "has both an OPERATION-kind and a RANK-kind (root) parameter, symmetric COUNT -- reduces to "
            "a single root only (reduce-shaped, not allreduce)",
            [buf_err, extent_note, root_note, scope_note],
        )

    if rank and buf and not asymmetric:
        source, dest, buf_err = _pick_source_dest_buffers(params)
        extent, extent_note = _extent_binding(params, function_key, type_family)
        root_sel, root_note = _root_selector(params)
        scope_sel, scope_note = _scope_selector(params)
        bindings = {"source_buffer": source, "dest_buffer": dest, "extent": extent,
                    "root_selector": root_sel, "scope_selector": scope_sel}
        return _shape_proposal(
            entry_key, "collective.one_to_all_uniform", bindings,
            "has a RANK-kind (root) and BUFFER-kind parameter(s), no OPERATION, symmetric COUNT -- "
            "broadcast-shaped (one root distributes identically to every member)",
            [buf_err, extent_note, root_note, scope_note],
        )

    # The gather_to_all / reduce_scatter profiles are
    # built shapes, so the asymmetric-COUNT case proposes instead of
    # escalating -- EXCEPT alltoall, whose doubly-indexed pairwise movement is
    # still a genuinely unrepresentable, logged gap (a name check is the
    # honest discriminator here: alltoall's parameter profile is otherwise
    # identical to allgather's).
    if asymmetric and "alltoall" not in function_key and buf and not rank:
        source, dest, buf_err = _pick_source_dest_buffers(params)
        scope_sel, scope_note = _scope_selector(params)
        scope_ref = _scope_param_ref(params)
        if op or name_op:
            slice_extent, ext_note = _prefixed_extent(params, ("recv",))
            op_ref = f"param:{op[0]['name']}" if op else f"literal:{name_op}"
            slice_offset = (
                f"rank_in({scope_ref}) * extent_size({slice_extent['count_ref']}, {slice_extent['datatype_ref']})"
                if slice_extent and scope_ref else None
            )
            return _shape_proposal(
                entry_key, "collective.reduce_scatter",
                {"source_buffer": source, "dest_buffer": dest, "slice_extent": slice_extent,
                 "operation": op_ref, "scope_selector": scope_sel, "slice_offset": slice_offset},
                "OPERATION signal plus an asymmetric (recv-prefixed) COUNT and no root -- each "
                "participant receives only its own slice of the reduced result (reduce_scatter-shaped, "
                "the reduced-source offset)",
                [buf_err, ext_note, scope_note,
                 None if slice_offset else "slice_offset could not be derived -- needs human completion"],
            )
        contribution_extent, c_note = _prefixed_extent(params, ("send",))
        block_extent, b_note = _prefixed_extent(params, ("recv",))
        placement_offset = (
            f"rank_in({scope_ref}) * extent_size({block_extent['count_ref']}, {block_extent['datatype_ref']})"
            if block_extent and scope_ref else None
        )
        return _shape_proposal(
            entry_key, "collective.gather_to_all",
            {"source_buffer": source, "dest_buffer": dest, "contribution_extent": contribution_extent,
             "block_extent": block_extent, "scope_selector": scope_sel, "placement_offset": placement_offset},
            "no OPERATION and no root, asymmetric send/recv-prefixed COUNT -- every participant "
            "assembles every contribution with no operator (allgather-shaped, the 'gathered' "
            "source kind)",
            [buf_err, c_note, b_note, scope_note,
             None if placement_offset else "placement_offset could not be derived -- needs human completion"],
        )

    reason = (
        "a doubly-indexed alltoall profile (pairwise movement -- still a genuinely unrepresentable, "
        "logged gap)" if asymmetric else
        "no RANK (root) and no OPERATION signal at all (the variable-length collect family and other "
        "unprofiled collectives land here)"
    )
    return _escalate_proposal(
        entry_key, None,
        f"collective call with {reason} -- see {_KNOWN_GAPS_REF}; not a heuristic failure on this "
        f"script's part",
    )


def _p2p_matching_binding(params):
    """(matching_object_or_None, note) for the p2p shapes' `matching` slot.

    2026-07-19: matching became a required literal_slot binding on all four
    point-to-point shapes (p2p.direct_send/direct_recv AND handle_bound.
    post_send/post_recv), replacing the old `extra`-patch mechanism -- the
    2026-07-19 design review found that every user of those shapes needed the
    same `extra` for correctness, which violated the catalog's own "extra is
    for genuinely one-off quirks" guardrail (docs/schema/shape-catalog.md's
    2026-07-19 decision note). Returns None (with a note) when no
    COMMUNICATOR+RANK pair exists to derive matching from -- _try_expand then
    reports the proposal as needs-human-completion rather than silently
    expanding with matching absent (which is exactly what the pre-slot
    handle_bound path used to do for any non-golden-matched function).
    """
    comm = _by_kind(params, "COMMUNICATOR")
    rank = _by_kind(params, "RANK")
    if not (comm and rank):
        return None, ("no COMMUNICATOR+RANK parameter pair to derive the required `matching` binding "
                      "from -- needs human completion")
    comm_ref, rank_ref = f"param:{comm[0]['name']}", f"param:{rank[0]['name']}"
    tag = _by_kind(params, "TAG")
    if tag:
        return ({
            "kind": "tag_match",
            "match_keys": [comm_ref, f"param:{tag[0]['name']}", rank_ref, "self_rank_as_source"],
            "matched_across": "paired_call",
            "program_order_required": False,
        }, "TAG-kind parameter present -- proposed tag_match (MPI-style) as the `matching` binding")
    return ({
        "kind": "peer_match",
        "match_keys": [comm_ref, rank_ref],
        "matched_across": "paired_call",
        "program_order_required": True,
    }, "no TAG-kind parameter -- proposed peer_match (NCCL-style, program-order-disambiguated in place "
       "of a tag) as the `matching` binding")


def _propose_point_to_point(entry_key, params, type_family=None):
    request = _by_kind(params, "REQUEST")
    buf = _by_kind(params, "BUFFER")
    extent, extent_note = _extent_binding(params, entry_key.split(":", 1)[1], type_family)
    matching, matching_note = _p2p_matching_binding(params)

    if request:
        handle_ref = f"param:{request[0]['name']}"
        if buf and buf[0].get("direction") == "in":
            bindings = {"buffer": f"param:{buf[0]['name']}", "extent": extent, "handle": handle_ref,
                        "matching": matching}
            return _shape_proposal(
                entry_key, "handle_bound.post_send", bindings,
                "REQUEST-kind parameter present, BUFFER-kind parameter is input-direction -- send-shaped",
                [extent_note, matching_note],
            )
        bindings = {"buffer": f"param:{buf[0]['name']}" if buf else None, "extent": extent, "handle": handle_ref,
                    "matching": matching}
        return _shape_proposal(
            entry_key, "handle_bound.post_recv", bindings,
            "REQUEST-kind parameter present, BUFFER-kind parameter is output-direction -- recv-shaped",
            [extent_note, matching_note],
        )

    # No REQUEST handle -- try the newer p2p.direct_send/direct_recv shapes (added
    # because mpi_send/mpi_recv/ncclSend/ncclRecv all hit this exact gap). Both shapes need a COMMUNICATOR + RANK (peer/dest/source) parameter
    # pair to derive the required `matching` binding from -- without those, there's
    # nothing to bind matching to and this still has to escalate.
    if buf and matching is not None:
        bindings = {"buffer": f"param:{buf[0]['name']}", "extent": extent, "matching": matching}
        if buf[0].get("direction") == "in":
            return _shape_proposal(
                entry_key, "p2p.direct_send", bindings,
                "no REQUEST handle, but a BUFFER (input-direction) + COMMUNICATOR + RANK parameter set is "
                "present -- send-shaped under the handle-free p2p shape",
                [extent_note, matching_note],
            )
        return _shape_proposal(
            entry_key, "p2p.direct_recv", bindings,
            "no REQUEST handle, but a BUFFER (output-direction) + COMMUNICATOR + RANK parameter set is "
            "present -- recv-shaped under the handle-free p2p shape",
            [extent_note, matching_note],
        )

    return _escalate_proposal(
        entry_key, None,
        "point-to-point call with no REQUEST handle and no clear BUFFER+COMMUNICATOR+RANK parameter set "
        "to derive p2p.direct_send/direct_recv's required `matching` binding from either -- genuine "
        "catalog gap, distinct from the now-covered blocking/stream-ordered case",
    )


# put vs. get, read off the function name. Both PGAS PPMs name these
# operations literally and without exception: shmem_put/shmem_get,
# nvshmem_putmem/nvshmem_getmem, shmem_ctx_get64_nbi, shmem_{T}_p (single-
# element put) / shmem_{T}_g (single-element get), and the strided/
# interleaved-block iput/iget/ibput/ibget families.
#
# **Why this replaced a blanket rma.put default (fixed 2026-07-21).** The old
# rule said "input BUFFER + output BUFFER -> rma.put" and never looked at the
# name, on the reasoning that parameter direction alone cannot disambiguate.
# That is true and was the wrong conclusion: the NAME disambiguates perfectly,
# and defaulting instead of reading it meant 55 of the corpus's 57 get-family
# functions were assigned the put shape. Only shmem_{T}_get and
# nvshmem_{T}_get escaped, and only because a hand-written golden example
# happened to cover those two exact names.
#
# The failure is not cosmetic. rma.put's template says the ORIGIN reads
# origin_buffer locally and the TARGET writes target_buffer remotely. A get
# binds source (the REMOTE buffer) to origin_buffer and dest (the LOCAL
# buffer) to target_buffer -- so the expansion asserted that the caller reads
# a remote address and that the remote PE writes into the caller's local
# memory, with the pe selector applied to the wrong side. A code generator
# lowering that emits a put where the program called a get; a verifier
# derives its data-equality obligation backwards.
_GET_NAME_RE = re.compile(r"(^|_)(i|ib)?get(mem|_nbi|\d*)|_g(\d+)?(_nbi)?$|_g$")
_PUT_NAME_RE = re.compile(r"(^|_)(i|ib)?put(mem|_nbi|\d*)|_p(\d+)?(_nbi)?$|_p$")


# Strided / interleaved-block RMA: shmem_iput/iget (element stride) and
# shmem_ibput/ibget (block stride). Anchored on the i/ib prefix immediately
# before put/get so an ordinary "..._put" never matches.
_STRIDED_NAME_RE = re.compile(r"_(i|ib)(put|get)(\d+|mem)?(_nbi)?(_|$)")


def _has_stride_params(params):
    """True when the signature carries OpenSHMEM's dst/sst stride pair."""
    names = {p.get("name", "").lower() for p in params}
    return "dst" in names and "sst" in names


def _rma_direction_from_name(function_key):
    """'put' | 'get' | None -- which RMA direction the name states outright."""
    lkey = function_key.lower()
    is_get = bool(_GET_NAME_RE.search(lkey))
    is_put = bool(_PUT_NAME_RE.search(lkey))
    if is_get and not is_put:
        return "get"
    if is_put and not is_get:
        return "put"
    return None  # neither, or ambiguous (both matched) -- don't guess


def _propose_one_sided(entry_key, params, type_family=None):
    dest = next((p for p in params if p.get("kind") == "BUFFER" and p.get("direction") == "out"), None)
    source = next((p for p in params if p.get("kind") == "BUFFER" and p.get("direction") == "in"), None)

    # --- the single-element put, whose source is an operand, not a buffer ---
    # shmem_{T}_p(dest, value, pe) / nvshmem_{T}_p write exactly one element
    # whose value arrives by value. There is no input BUFFER, so the pair test
    # below rejects them and they escalated (26 families, the largest
    # escalation group that was not already a logged schema gap). rma.put
    # genuinely does not fit -- its df_read reads an origin_buffer these calls
    # do not have, and its extent slot has nothing to bind to -- so this is a
    # shape of its own, rma.put_scalar, modelled on how rma.atomic already
    # handles a by-value operand. Authored 2026-07-21.
    if dest and not source:
        function_key = entry_key.split(":", 1)[1]
        operand = next((p for p in params if p.get("kind") == "SCALAR"
                        and p.get("name", "").lower() in ("value", "val")), None)
        if operand and _PUT_NAME_RE.search(function_key.lower()):
            target_sel, target_note = _target_selector(params)
            return _shape_proposal(
                entry_key, "rma.put_scalar",
                {"target_buffer": f"param:{dest['name']}",
                 "value": f"param:{operand['name']}",
                 "target_selector": target_sel},
                "single-element put: the written value is a by-value operand rather than a local "
                "buffer, so rma.put's origin-side read and extent have nothing to bind to -- "
                "rma.put_scalar reads the operand at the origin and sources the target's write "
                "from it structurally, the same way rma.atomic handles its operand",
                [target_note],
            )

    if not (dest and source):
        return _escalate_proposal(entry_key, None, "one_sided call without a clear input/output BUFFER pair")

    function_key = entry_key.split(":", 1)[1]
    extent, extent_note = _extent_binding(params, function_key, type_family)
    target_sel, target_note = _target_selector(params)
    direction = _rma_direction_from_name(function_key)

    # --- strided RMA escalates rather than being described as contiguous ---
    # shmem_iput/iget and shmem_ibput/ibget move nelems elements separated by
    # a per-side stride (dst/sst). data_flow describes one whole buffer with
    # one extent and has no stride concept at all, so binding these to the
    # contiguous rma.put/rma.get shape produces an entry that claims a dense
    # transfer where the real one is sparse -- a wrong fit, not a partial one,
    # and one a race detector would use to compute overlapping ranges that do
    # not overlap in reality. 50 corpus functions; logged as a real gap in
    # docs/cross-ppm-analysis/known-gaps-and-open-questions.md rather than
    # papered over (2026-07-21 full-corpus audit).
    if _STRIDED_NAME_RE.search(function_key.lower()) or _has_stride_params(params):
        return _escalate_proposal(
            entry_key, None,
            "strided RMA (iput/iget/ibput/ibget): the call moves `nelems` elements separated by an "
            "explicit per-side stride, which data_flow's single-extent model cannot express -- "
            "assigning the contiguous rma.put/rma.get shape would describe a dense transfer the call "
            "does not perform. Needs either a stride-carrying extent or a dedicated strided shape",
        )

    # --- put-with-signal gets its own shape, not a plain put ---------------
    sig_addr = next((p for p in params if p.get("name", "").lower() == "sig_addr"), None)
    sig_op = next((p for p in params if p.get("name", "").lower() == "sig_op"), None)
    signal = next((p for p in params if p.get("name", "").lower() == "signal"), None)
    if direction == "put" and sig_addr and sig_op and signal:
        bindings = {"origin_buffer": f"param:{source['name']}", "target_buffer": f"param:{dest['name']}",
                    "extent": extent, "target_selector": target_sel,
                    "signal_buffer": f"param:{sig_addr['name']}",
                    "signal_operand": f"param:{signal['name']}",
                    "signal_op": f"param:{sig_op['name']}"}
        return _shape_proposal(
            entry_key, "rma.put_signal", bindings,
            "put-with-signal: an rma.put plus a separately-addressed read_modify_write on the target's "
            "signal object (sig_addr/signal/sig_op) -- the plain rma.put shape would drop all three, "
            "which is the entire difference between this call and an ordinary put",
            [extent_note, target_note],
        )

    if direction == "get":
        # A get moves data the other way, so the two buffer slots swap roles:
        # the REMOTE buffer (the `source`/in-direction parameter, which names
        # an address on the target PE) is what the target reads, and the LOCAL
        # buffer (`dest`) is what the origin writes.
        bindings = {"origin_buffer": f"param:{dest['name']}", "target_buffer": f"param:{source['name']}",
                    "extent": extent, "target_selector": target_sel}
        return _shape_proposal(
            entry_key, "rma.get", bindings,
            "one_sided call whose name states the get direction outright -- rma.get, with the remote "
            "(in-direction) buffer bound to the target side and the local (out-direction) buffer to the "
            "origin side",
            [extent_note, target_note],
        )

    if direction == "put":
        bindings = {"origin_buffer": f"param:{source['name']}", "target_buffer": f"param:{dest['name']}",
                    "extent": extent, "target_selector": target_sel}
        return _shape_proposal(
            entry_key, "rma.put", bindings,
            "one_sided call whose name states the put direction outright -- rma.put (origin reads its "
            "local buffer, target is written remotely)",
            [extent_note, target_note],
        )

    return _escalate_proposal(
        entry_key, None,
        "one_sided call with an input/output BUFFER pair but no put/get direction recoverable from the "
        "function name -- parameter direction alone cannot disambiguate which way the data moves, and "
        "guessing inverts the transfer for exactly half the cases, so this escalates instead of "
        "defaulting (see _rma_direction_from_name for the 2026-07-21 audit that forced this)",
    )


def propose_for_entry(entry_key, entry, golden_index):
    model, function_key = entry_key.split(":", 1)
    name_lower = function_key.lower()
    api_group = entry["identity"]["api_group"]
    params = entry["parameters"]
    type_family = entry["identity"].get("type_family")

    golden = golden_index.get((model, function_key))
    if golden is not None:
        return _proposal_from_golden(entry_key, golden)

    if api_group in ("query", "management"):
        # mpi_init/mpi_finalize/shmem_init/shmem_finalize fall through to here too, now that
        # Heuristic Classification tags all four "management" (2026-07-17 fix). A dedicated
        # escalate_new_shape special case used to single these out with "needs a human decision
        # on whether to model an implicit environment handle" -- reviewed and confirmed
        # 2026-07-17:
        # no_formal_applicable is the right answer, consistent with every other query/management
        # call and with shmem_init/finalize's own pre-existing precedent. The special case was
        # removed rather than left as dead code.
        return _no_formal_proposal(
            entry_key,
            f"identity.api_group='{api_group}' -- matches the established convention that query/"
            f"management calls carry no semantics.formal (explicit non-goal, not a gap; see "
            f"{_KNOWN_GAPS_REF}, Non-goals)",
        )

    if name_lower in ("mpi_comm_rank", "mpi_comm_size", "nvshmem_my_pe", "nvshmem_n_pes"):
        return _no_formal_proposal(
            entry_key,
            "pure local query call (rank/size/PE-id inquiry) -- Heuristic Classification did not tag "
            "identity.api_group here, but the function is unambiguously a query call by shape and name",
        )

    if name_lower in ("ncclgroupstart", "ncclgroupend"):
        return _no_formal_proposal(
            entry_key,
            f"no parameters, no return payload -- matches the logged gap that "
            f"ncclGroupStart/End are deliberately left unmodeled rather than forced into a shape "
            f"({_KNOWN_GAPS_REF})",
        )

    if "wait_until" in name_lower:
        return _escalate_proposal(
            entry_key, None,
            f"polls a local memory location (ivar/cmp/cmp_value-style params), not a REQUEST handle -- "
            f"this is exactly the already-logged '_nbi family has no handle to bind completion to' gap "
            f"({_KNOWN_GAPS_REF}); handle_bound.wait_on_handle would be a forced fit, not a real match",
        )

    if api_group == "collective":
        return _propose_collective(entry_key, params, function_key, type_family)

    if api_group == "point_to_point":
        return _propose_point_to_point(entry_key, params, type_family)

    if api_group == "one_sided":
        return _propose_one_sided(entry_key, params, type_family)

    if name_lower.endswith("fence") or name_lower.endswith("quiet"):
        note = None
        if name_lower.endswith("quiet"):
            note = (
                "quiet and fence are related but distinct SHMEM/NVSHMEM ordering primitives (quiet waits "
                "for completion of all outstanding operations; fence only orders subsequent ones) -- "
                "reusing sync_only.local_fence for both may be a forced fit worth a human call, not a "
                "confirmed match"
            )
        return _shape_proposal(
            entry_key, "sync_only.local_fence", {},
            "self-only ordering point event, no participants beyond the caller and no data_flow -- "
            "matches the sync_only.local_fence pattern" + (f" ({note})" if note else ""),
        )

    return _escalate_proposal(
        entry_key, None,
        "no identity.api_group signal and no name-based rule matched -- no candidate shape identified",
    )


def _unbound_param_note(entry, bindings, extra=None):
    """Not every parameter the binder skips is a problem (ierror/status carry no
    formal-layer-relevant information), but silently dropping something like SHMEM's
    active-set arguments (PE_start/logPE_stride/PE_size/pSync) would hide a real
    scope-selector limitation from whoever reviews this proposal -- so name it
    explicitly rather than let the binding merely look complete.

    Scans `extra` too (added 2026-07-17, found auditing the pilot corpus): a
    tag_match/peer_match sync.matching extra references comm/dest/tag/source
    via match_keys, not bindings -- before this fix, every mpi_send/mpi_recv/
    mpi_isend-style proposal falsely flagged those as "not referenced by any
    binding" even though they're used, just via the extra mechanism rather
    than a bindings slot."""
    referenced = set(re.findall(r"param:([A-Za-z_][A-Za-z0-9_]*)", json.dumps(bindings)))
    if extra:
        referenced |= set(re.findall(r"param:([A-Za-z_][A-Za-z0-9_]*)", json.dumps(extra)))
    all_names = {p["name"] for p in entry["parameters"] if p.get("kind") != "ERROR_CODE"}
    unbound = sorted(all_names - referenced)
    if not unbound:
        return None
    return (
        f"parameter(s) {unbound} are not referenced by any binding -- confirm they're genuinely "
        f"irrelevant to the formal-layer semantics rather than silently dropped information"
    )


def _try_expand(proposal, shapes_by_id):
    if proposal["outcome"] != "shape_assigned":
        proposal["expansion"] = None
        proposal["expansion_error"] = None
        return proposal

    bindings = proposal["bindings"] or {}
    if any(v is None for v in bindings.values()):
        proposal["expansion"] = None
        proposal["expansion_error"] = (
            "bindings incomplete -- one or more slots could not be filled by the heuristic binder "
            "(see binder_notes); needs human completion before expansion can run"
        )
        return proposal

    shape = shapes_by_id.get(proposal["shape_ref"])
    if shape is None:
        proposal["expansion"] = None
        proposal["expansion_error"] = f"unknown shape_ref '{proposal['shape_ref']}' -- not in curated/shapes/shapes.json"
        return proposal

    try:
        expansion = expand_entry(shape, bindings, proposal.get("extra"))
        validate_formal(expansion)
        proposal["expansion"] = expansion
        proposal["expansion_error"] = None
    except (KeyError, FormalValidationError) as e:
        proposal["expansion"] = None
        proposal["expansion_error"] = str(e)
    return proposal


def _group_signature(proposal):
    """The review-grouping key: proposals that made the same decision for the
    same reason are one review unit, not N. Bindings are deliberately NOT part
    of the signature (they differ per function by construction) -- what a
    reviewer approves per group is the decision pattern; the record lists
    the review record lists every member and one fully-worked exemplar, so
    spot-checking individual bindings inside an approved group stays possible."""
    return (
        proposal["outcome"],
        proposal.get("shape_ref"),
        proposal["rationale"],
        tuple(sorted(n for n in proposal.get("binder_notes", []) if n)),
        proposal.get("expansion_error"),
    )


def _group_id(sig):
    """Stable id for a decision pattern, so a recorded decision survives a
    re-run. Derived from the signature itself rather than a position, because
    proposals get added and reordered constantly; if the pattern's own wording
    changes the id changes with it, and the old decision surfaces as orphaned
    rather than being silently reapplied to something a human never read."""
    outcome = sig[0]
    digest = hashlib.sha1(json.dumps(sig, sort_keys=True, default=list).encode()).hexdigest()
    return f"{outcome}:{digest[:8]}"


def _build_review_groups(proposals):
    """Group the corpus-scale proposal list into review units.

    This is the scaling answer to the
    'what does review look like at thousands of proposals' question, for the
    Assignment component specifically: a human reads GROUPS (decision pattern
    + one exemplar + the member list) and records one decision per group,
    rather than reading ~980 proposals one at a time.
    """
    groups = {}
    for p in proposals:
        sig = _group_signature(p)
        g = groups.setdefault(sig, {"members": [], "exemplar": None})
        g["members"].append(p["entry_key"])
        if g["exemplar"] is None:
            g["exemplar"] = p
    worksheet = []
    for sig, g in groups.items():
        outcome, shape_ref, rationale, notes, expansion_error = sig
        worksheet.append({
            "group_id": _group_id(sig),
            "outcome": outcome,
            "shape_ref": shape_ref,
            "rationale": rationale,
            "binder_notes": list(notes),
            "expansion_error": expansion_error,
            "member_count": len(g["members"]),
            "members": g["members"],
            "exemplar": g["exemplar"],
        })
    worksheet.sort(key=lambda w: (-w["member_count"], w["outcome"], w["shape_ref"] or ""))
    return worksheet


def _write_review_record(groups, generated_at):
    """Delegates the merge-forward half to workflow/review/record.py, which is
    shared with the shapes and supplement records so a decision can never be
    treated differently depending on which artifact it belongs to."""
    return merge_and_write(
        path=_REVIEW_PATH,
        reviews="curated/formal-assignments.json",
        groups=groups,
        comment=(
            "Review record for curated/formal-assignments.json. One group per DECISION PATTERN "
            "(outcome + shape_ref + rationale + binder notes), with every member and one "
            "fully-worked exemplar, so ~980 proposals collapse to a readable number of "
            "decisions. group_id hashes the pattern itself, so a reworded rationale yields a "
            "new, unreviewed group rather than carrying an old decision onto something nobody "
            "read. " + BOILERPLATE),
        generated_at=generated_at,
    )


def _group_signature(proposal):
    """The review-grouping key: proposals that made the same decision for the
    same reason are one review unit, not N. Bindings are deliberately NOT part
    of the signature (they differ per function by construction) -- what a
    reviewer approves per group is the decision pattern; the record lists
    the review record lists every member and one fully-worked exemplar, so
    spot-checking individual bindings inside an approved group stays possible."""
    return (
        proposal["outcome"],
        proposal.get("shape_ref"),
        proposal["rationale"],
        tuple(sorted(n for n in proposal.get("binder_notes", []) if n)),
        proposal.get("expansion_error"),
    )


def _group_id(sig):
    """Stable id for a decision pattern, so a recorded decision survives a
    re-run. Derived from the signature itself rather than a position, because
    proposals get added and reordered constantly; if the pattern's own wording
    changes the id changes with it, and the old decision surfaces as orphaned
    rather than being silently reapplied to something a human never read."""
    outcome = sig[0]
    digest = hashlib.sha1(json.dumps(sig, sort_keys=True, default=list).encode()).hexdigest()
    return f"{outcome}:{digest[:8]}"


def _build_review_groups(proposals):
    """Group the corpus-scale proposal list into review units.

    This is the scaling answer to the
    'what does review look like at thousands of proposals' question, for the
    Assignment component specifically: a human reads GROUPS (decision pattern
    + one exemplar + the member list) and records one decision per group,
    rather than reading ~980 proposals one at a time.
    """
    groups = {}
    for p in proposals:
        sig = _group_signature(p)
        g = groups.setdefault(sig, {"members": [], "exemplar": None})
        g["members"].append(p["entry_key"])
        if g["exemplar"] is None:
            g["exemplar"] = p
    worksheet = []
    for sig, g in groups.items():
        outcome, shape_ref, rationale, notes, expansion_error = sig
        worksheet.append({
            "group_id": _group_id(sig),
            "outcome": outcome,
            "shape_ref": shape_ref,
            "rationale": rationale,
            "binder_notes": list(notes),
            "expansion_error": expansion_error,
            "member_count": len(g["members"]),
            "members": g["members"],
            "exemplar": g["exemplar"],
        })
    worksheet.sort(key=lambda w: (-w["member_count"], w["outcome"], w["shape_ref"] or ""))
    return worksheet


def run():
    """Corpus-only (2026-07-21): instances/1_syntactic-semantics-api.json ->
    curated/formal-assignments.json, plus the grouped review record
    (curated/review/formal-assignments.review.json) so the review surface is
    decision-pattern groups, not hundreds of individual proposals. That record
    is merged, never overwritten: statuses a human has already set survive a
    re-run, and decisions whose group no longer exists move to
    orphaned_decisions rather than disappearing.
    Output is proposals-only -- nothing promotes it into entries here."""
    in_path = _SEMANTICS_API_PATH
    out_path = _OUT_PATH

    with open(_SHAPES_PATH) as f:
        shapes = json.load(f)
    shapes_by_id = {s["id"]: s for s in shapes}

    with open(_SEED_PATH) as f:
        seed = json.load(f)["assignments"]
    golden_index = {(a["ppm"], a["function"]): a for a in seed}

    with open(in_path) as f:
        classified = json.load(f)

    proposals = []
    for entry_key in sorted(classified):
        entry = classified[entry_key]
        proposal = propose_for_entry(entry_key, entry, golden_index)
        if proposal["outcome"] == "shape_assigned":
            note = _unbound_param_note(entry, proposal["bindings"] or {}, proposal.get("extra"))
            if note:
                proposal["binder_notes"].append(note)
        proposal = _try_expand(proposal, shapes_by_id)
        proposals.append(proposal)

    outcome_counts = {}
    expansion_ok = 0
    for p in proposals:
        outcome_counts[p["outcome"]] = outcome_counts.get(p["outcome"], 0) + 1
        if p["outcome"] == "shape_assigned" and p.get("expansion") is not None:
            expansion_ok += 1

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "total": len(proposals),
            "by_outcome": outcome_counts,
            "shape_assigned_with_valid_expansion": expansion_ok,
        },
        "proposals": proposals,
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"wrote {len(proposals)} proposals to {out_path}")
    print(f"by outcome: {outcome_counts}")
    print(f"shape_assigned with a valid expansion: {expansion_ok}")

    groups = _build_review_groups(proposals)
    summary = _write_review_record(groups, out["generated_at"])
    print(f"review record: {summary['groups']} decision-pattern groups "
          f"({summary['reviewed']} carrying an existing decision, {summary['new']} new, "
          f"{summary['orphaned']} orphaned) -> {_REVIEW_PATH}")

    print("every proposal is confidence='needs_approval' -- none of this is shipped output; "
          "a human must read and promote each one, see this module's own docstring")
    return 0


if __name__ == "__main__":
    sys.exit(run())
