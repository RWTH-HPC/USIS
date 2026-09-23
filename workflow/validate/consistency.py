"""
Cross-entry consistency checking -- the first built piece of the Validate
component (workflow/README.md).

Per-entry schema validation (workflow/extract/validate_entry.py) can never
see relationships BETWEEN entries; this module checks exactly those, plus
the per-entry string surfaces the schema types as plain strings:

  1. relationships.variants symmetry -- if A.variants.nonblocking == B,
     then B.variants.blocking should name A back (and persistent/blocking
     the same way). An asymmetry is either a heuristic miss or a real
     naming-convention irregularity; either way a human should see it.
  2. relationships.variants / relationships.superseded_by /
     relationships.supersedes are model-qualified ("model:function_key",
     enforced as of 2026-07-22 -- the bare intra-model form the corpus used
     to emit is now a finding) and their targets exist in the named model's
     corpus -- dangling references are always a bug (Heuristic
     Classification's _variants contract says it never fabricates a name)
     -- plus
     superseded_by/supersedes symmetry, since supersedes is derived by
     inverting superseded_by and any asymmetry means that derivation is
     broken.
  3. parameters[].length follows the length convention (docs/schema/
     field-semantics.md): a string is a sibling parameter's name, a PPM
     constant or "*", and array_type is null exactly when length is.
  4. semantics.formal grammar conformance (workflow/formal/grammar.py's
     validate_formal_grammar) and matched.via resolution -- every
     source.kind=="matched" via must name a sync.events id in the same
     formal block (the convention docs/schema/semantics-formal.md made
     official 2026-07-19).

Since 2026-08-06 this is also the Validate STAGE of the chain, not only a
hand-run checker: under --report it additionally re-validates every entry of
the finished corpus against the strict schema and writes both results to
instances/validate-report.json. Re-validating rather than transcribing
assemble.py's own inline result is the point of having a stage -- a check that
copies another step's answer cannot disagree with it, and disagreeing is what a
check is for.

Pure checks, no mutation, no model calls. Findings are reported, never
auto-fixed -- this is Validate's flag-for-Review side, not a fixer. Entries are
never dropped: an entry that fails the strict schema still ships, and the
report says which and why.

Run: python3 workflow/validate/consistency.py            (merged corpus, exit 1 on findings)
     python3 workflow/validate/consistency.py --report   (also the final corpus; writes the report)
"""

import argparse
import datetime
import json
import os
import sys

_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "workflow", "formal"))
sys.path.insert(0, os.path.join(_ROOT, "workflow", "extract"))

from grammar import validate_formal_grammar, GrammarError  # noqa: E402
from validate_entry import validate_entry, ValidationError  # noqa: E402

_LAYOUT_COMMON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common")
sys.path.insert(0, _LAYOUT_COMMON)
from layout import OUT_DIR, SCHEMAS_DIR  # noqa: E402

_MERGED_PATH = os.path.join(OUT_DIR, "3_syntactic-semantics-formal-supplement-api.json")
_FINAL_PATH = os.path.join(OUT_DIR, "4_final-api.json")
_API_SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "api-schema.json")
_REPORT_PATH = os.path.join(OUT_DIR, "validate-report.json")

# variants keys that form reciprocal pairs. neighborhood/host/gpu have no
# defined reciprocal key in the 6-key vocabulary (a neighborhood variant
# points back via... nothing -- there is no "non-neighborhood" key), so only
# existence is checked for those, not symmetry. "blocking" is the one
# many-to-one key: BOTH a nonblocking (I-prefix) and a persistent (_init)
# variant point back to the same base via "blocking", so its acceptable
# reciprocals are {nonblocking, persistent} -- the checker's own first run
# flagged every _init function before this was modeled correctly.
_RECIPROCAL = {
    "nonblocking": ("blocking",),
    "persistent": ("blocking",),
    "blocking": ("nonblocking", "persistent"),
}


def _split(reference):
    """"model:function_key" -> (model, function_key). None if unqualified.

    Every cross-entry reference in the schema is documented as
    "model:function_key", and as of 2026-07-22 that is enforced rather than
    merely documented: the bare intra-model form the corpus used to emit
    (`"mpi_iallgather"`) is now a finding, not an accepted alternative. It
    was a real inconsistency -- the schema descriptions, the shipped
    docs/schema/examples/mpi-api.json example, and the generated corpus disagreed, and
    nothing caught it because this checker had been written to match the
    corpus rather than the schema. Qualifying at the source
    (workflow/classify/emit.py's _qualify) also makes cross-PPM references
    expressible, which the bare form structurally could not represent.
    """
    if ":" not in reference:
        return None
    model, function_key = reference.split(":", 1)
    return model, function_key


def _family_matcher(names):
    """Set of concrete names + regexes for collapsed {T}/{CT} family names, so
    a CONCRETE reference (e.g. post-Concretize 'nvshmem_bfloat16_put_nbi')
    still counts as existing when the universe carries only the collapsed
    family entry ('nvshmem_{T}_put_nbi')."""
    import re as _re
    exact = set(names)
    patterns = [
        _re.compile("^" + _re.escape(n).replace(_re.escape("{T}"), "[a-z0-9]+")
                    .replace(_re.escape("{CT}"), "[a-z0-9 ]+") + "$")
        for n in names if "{T}" in n or "{CT}" in n
    ]

    def known(name):
        return name in exact or any(p.match(name) for p in patterns)

    return known


def check_corpus(entries, universe=None):
    """{entry_key: entry} -> list of finding strings (empty = clean).

    `universe` (default: `entries` itself) is the corpus existence/symmetry
    checks resolve against -- pass the full merged corpus when checking a
    SUBSET, otherwise every reference out of the subset is a false
    dangling-target finding (the checker's first run on a 42-function subset
    produced 107 of them)."""
    findings = []
    universe = universe if universe is not None else entries
    by_model = {}
    for key in universe:
        model, function_key = key.split(":", 1)
        by_model.setdefault(model, set()).add(function_key)
    known_by_model = {m: _family_matcher(names) for m, names in by_model.items()}

    for key, entry in sorted(entries.items()):
        model, function_key = key.split(":", 1)

        def resolve(reference, path):
            """(reference, its field path) -> target entry_key, or None after
            appending the appropriate finding. Shared by every cross-entry
            reference below so the qualified-form rule is stated once."""
            parts = _split(reference)
            if parts is None:
                findings.append(f"{key}: {path} names {reference!r}, which is not model-qualified -- "
                                f"every cross-entry reference must be \"model:function_key\" "
                                f"(did you mean {model}:{reference}?)")
                return None
            target_model, target_function_key = parts
            target_known = known_by_model.get(target_model)
            if target_known is None or not target_known(target_function_key):
                findings.append(f"{key}: {path} names {reference!r}, "
                                f"which does not exist in the {target_model} corpus")
                return None
            return f"{target_model}:{target_function_key}"

        # --- 1+2: variants existence and symmetry
        variants = (entry.get("relationships") or {}).get("variants") or {}
        for vkey, target in variants.items():
            if target is None:
                continue
            target_key = resolve(target, f"relationships.variants.{vkey}")
            if target_key is None:
                continue
            reciprocal_keys = _RECIPROCAL.get(vkey)
            if reciprocal_keys is None:
                continue
            target_entry = universe.get(target_key)
            if target_entry is None:
                continue  # exists only via a collapsed family pattern -- symmetry not checkable at this granularity
            target_variants = (target_entry.get("relationships") or {}).get("variants") or {}
            backs = {rk: target_variants.get(rk) for rk in reciprocal_keys}
            if key not in backs.values():
                findings.append(
                    f"{key}: variants.{vkey}={target!r} but {target_key}'s "
                    f"{'/'.join(reciprocal_keys)} back-reference(s) are {backs} "
                    f"(none names {key!r}) -- asymmetric"
                )

        # --- 2b: superseded_by targets. relationships is the only
        # supersession edge, and supersedes -- its mechanically
        # derived inverse -- is checked alongside it. supersedes is derived
        # rather than authored, so a dangling or asymmetric entry there
        # means the deriving code is wrong, not the data; that's exactly
        # why it's worth checking rather than trusting.
        rel = entry.get("relationships") or {}
        superseded_by = rel.get("superseded_by")
        if superseded_by is not None:
            resolve(superseded_by, "relationships.superseded_by")

        for i, source in enumerate(rel.get("supersedes") or []):
            source_key = resolve(source, f"relationships.supersedes[{i}]")
            if source_key is None:
                continue
            source_entry = universe.get(source_key)
            if source_entry is None:
                continue  # exists only via a collapsed family pattern -- symmetry not checkable here
            back = (source_entry.get("relationships") or {}).get("superseded_by")
            if back != key:
                findings.append(f"{key}: relationships.supersedes[{i}]={source!r} but that entry's "
                                f"superseded_by is {back!r} (does not name {key!r}) -- asymmetric; "
                                f"supersedes is derived, so this means the inverse-index step is wrong")

        # --- 3: the length convention. A string length is a sibling
        # parameter's name, a PPM constant (MPI_MAX_OBJECT_NAME) or "*"; and
        # length and array_type are null together, since null means "not an
        # array" in both.
        param_names = {p.get("name") for p in entry.get("parameters") or []}
        for i, p in enumerate(entry.get("parameters") or []):
            length, array_type = p.get("length"), p.get("array_type")
            if (length is None) != (array_type is None):
                findings.append(f"{key}: parameters[{i}] has length={length!r} but "
                                f"array_type={array_type!r} -- both are null exactly for a non-array")
            if not isinstance(length, str) or length in param_names or length == "*":
                continue
            if length.isupper():
                continue  # PPM constant bound
            findings.append(f"{key}: parameters[{i}].length references {length!r}, "
                            f"not a parameter of this entry")

        # --- 4: formal grammar + matched.via resolution
        formal = (entry.get("semantics") or {}).get("formal")
        if formal:
            try:
                for err in validate_formal_grammar(formal):
                    findings.append(f"{key}: {err}")
            except GrammarError as e:
                findings.append(f"{key}: {e}")
            event_ids = {ev.get("id") for ev in (formal.get("sync") or {}).get("events") or []}
            for i, df in enumerate(formal.get("data_flow") or []):
                source = df.get("source")
                if isinstance(source, dict) and source.get("kind") == "matched":
                    via = source.get("via")
                    if via not in event_ids:
                        findings.append(f"{key}: data_flow[{i}].source.via={via!r} does not resolve to a "
                                        f"sync.events id in the same formal block (have {sorted(event_ids)})")

        # --- 5: return.value_kind only on a returned value. The
        # schema cannot state this -- it has no conditionals, and neither does
        # the in-house validator -- and RANK on an ERROR_CODE return would tell
        # a consumer the status code is a rank.
        ret = entry.get("return") or {}
        if ret.get("value_kind") is not None and ret.get("kind") != "value":
            findings.append(f"{key}: return.value_kind={ret['value_kind']!r} but return.kind is "
                            f"{ret.get('kind')!r} -- value_kind describes a returned value only")

    return findings


def check_strict_schema(entries):
    """Every concrete entry of the finished corpus against the strict schema.
    Returns {entry_key: message} for the ones that fail. Failures are expected
    and informational: the ~24 pure-prose semantic fields are only populated
    for the functions the supplement covers, so every other entry is missing a
    required field. The report says so rather than the corpus hiding it."""
    with open(_API_SCHEMA_PATH) as f:
        schema = json.load(f)
    errors = {}
    for key in sorted(entries):
        try:
            validate_entry(entries[key], schema)
        except ValidationError as e:
            errors[key] = str(e)
    return errors


def run(write_report=False):
    with open(_MERGED_PATH) as f:
        entries = json.load(f)
    findings = check_corpus(entries)
    print(f"merged corpus: {len(entries)} entries, {len(findings)} finding(s)")

    for x in findings:
        print(f"  - {x}")

    if not write_report:
        return 1 if findings else 0

    if not os.path.exists(_FINAL_PATH):
        raise SystemExit(f"{_FINAL_PATH} not found -- run the assemble stage first")
    with open(_FINAL_PATH) as f:
        final = json.load(f)
    concrete = final.get("entries", {})
    schema_errors = check_strict_schema(concrete)
    print(f"final corpus: {len(concrete)} concrete entries, "
          f"{len(concrete) - len(schema_errors)} valid against the strict schema, "
          f"{len(schema_errors)} failing")

    # The stage's own cross-check: assemble.py validates inline as it writes,
    # and this re-validates the file it wrote. The two disagreeing would mean
    # the corpus on disk is not what assemble thinks it produced.
    reported = set(final.get("validation_errors") or {})
    drift = sorted(set(schema_errors) ^ reported)
    if drift:
        print(f"  ! {len(drift)} entr{'y' if len(drift) == 1 else 'ies'} disagree with "
              f"4_final-api.json's own validation_errors, e.g. {drift[0]}")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(_REPORT_PATH, "w") as f:
        json.dump({
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                     .replace(microsecond=0).isoformat(),
            "note": ("Validate's two checks over the finished corpus: cross-entry consistency "
                     "(reference resolution, variants/supersedes symmetry, length references, "
                     "semantics.formal grammar) and per-entry strict-schema conformance. "
                     "Findings are reported, never auto-fixed, and no entry is dropped."),
            "summary": {
                "consistency_findings": len(findings),
                "concrete_entries": len(concrete),
                "entries_valid_against_strict_schema": len(concrete) - len(schema_errors),
                "entries_failed_validation": len(schema_errors),
                "disagreements_with_assemble": len(drift),
            },
            "consistency_findings": findings,
            "schema_validation_errors": schema_errors,
            "disagreements_with_assemble": drift,
        }, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"wrote {_REPORT_PATH}")

    # As a chain stage this is informational: a corpus with known gaps is the
    # expected state, and failing the build on it would make every build red.
    # The standalone --check invocation keeps the non-zero exit.
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="workflow/validate/consistency.py",
        description="Cross-entry consistency and strict-schema conformance over the corpus.")
    p.add_argument("--report", action="store_true",
                   help="also re-validate the final corpus against the strict schema and write "
                        "instances/validate-report.json; exits 0 even with findings (this is "
                        "what the chain's validate stage runs)")
    args = p.parse_args(argv)
    return run(write_report=args.report)


if __name__ == "__main__":
    sys.exit(main())
