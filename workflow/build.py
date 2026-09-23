#!/usr/bin/env python3
"""
One entry point for the generation workflow: raw PPM sources -> 4_final-api.json.

This is a driver, not a stage. It owns no logic of its own beyond ordering,
preflighting and the curated-artifact guard below -- every stage is still the
same standalone script it always was (workflow/extract/cli.py and friends),
runnable on its own, and this wrapper only ever invokes them in a subprocess.
Nothing here can change what a stage produces.

The chain (see workflow/README.md for the long form):

    extract     -> 0_syntactic-api.json                       + extract-report.json
    classify    -> 1_syntactic-semantics-api.json             + classify-report.json
    assign      -> curated/formal-assignments.json            [CURATED]
                   + curated/review/formal-assignments.review.json
    assemble    -> 2_..., 3_..., 4_final-api.json

## Three roots

    external-inputs/  third-party sources        --external-inputs DIR
    curated/          hand-authored/corrected    --curated-dir DIR
    instances/        everything a build writes  --out DIR

These are passed to the stage scripts as environment variables, resolved by
workflow/common/layout.py -- so every stage keeps working standalone with the
same defaults, and a redirected build needs no per-stage flags. The output
directory is created if it doesn't exist.

## Curated artifacts

`curated/formal-assignments.json` holds shape-assignment proposals a human
reads, corrects and ships. Regenerating it silently on every build would throw
those corrections away, and unlike the supplement proposals there is no
hand-authored upstream file for a correction to live in instead. So this
wrapper does NOT run its stage by default -- it consumes what is on disk, the
way a downstream user would. Regenerating is explicit and backed up:

    python3 workflow/build.py --regenerate formal

The one exception is bootstrap: if a curated artifact does not exist at all,
there are no edits to lose, so its stage runs automatically (--no-bootstrap
turns that into an error instead).

The curated supplement inputs (curated/supplement/supplement-<ppm>.json) need
no such guard: they are read directly by the assemble stage, which projects
them onto the corpus in memory. There is no supplement-proposals.json to
regenerate or protect (removed 2026-07-22).

"""

import argparse
import datetime
import os
import shutil
import subprocess
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "workflow", "common"))


class Stage:
    """`outputs`/`inputs` are (root, relative-path) pairs, where root is one of
    layout.py's three roots -- not plain paths, since where an artifact lives
    depends on --out/--curated-dir/--external-inputs at call time."""

    def __init__(self, name, script, summary, inputs, outputs, curated=False, args=None):
        self.name = name
        self.script = script
        self.summary = summary
        self.inputs = inputs
        self.outputs = outputs
        self.curated = curated
        # Fixed arguments a stage always runs with. Not a general escape hatch
        # for per-invocation options -- those still belong in the environment,
        # per layout.py -- but consistency.py doubles as the hand-run --check
        # tool, where the exit-on-findings behaviour has to differ.
        self.args = list(args or [])
        self.bootstrap = False


OUT, CURATED, EXTERNAL = "out", "curated", "external"

# Ordered. The wrapper never reorders these; --from/--to/--only/--skip only
# ever select a sub-list of this sequence.
STAGES = [
    Stage(
        name="extract",
        script="workflow/extract/cli.py",
        summary="Mechanical syntactic extraction from external-inputs/ (tex, headers, docs mirrors).",
        inputs=[(CURATED, "schemas/api-schema.json")],
        outputs=[(OUT, "0_syntactic-api.json"), (OUT, "extract-report.json")],
    ),
    Stage(
        name="classify",
        script="workflow/classify/cli.py",
        summary="Heuristic Classification: the 9 semantic_heuristic-tier fields, overlaid on 0_.",
        inputs=[(OUT, "0_syntactic-api.json")],
        outputs=[(OUT, "1_syntactic-semantics-api.json"), (OUT, "classify-report.json")],
    ),
    Stage(
        name="assign",
        script="workflow/formal/assign.py",
        summary="Shape assignment: proposes a semantics.formal shape per function family.",
        inputs=[(OUT, "1_syntactic-semantics-api.json"), (CURATED, "shapes/shapes.json")],
        outputs=[(CURATED, "formal-assignments.json"),
                 (CURATED, "review/formal-assignments.review.json")],
        curated=True,
    ),
    Stage(
        name="assemble",
        script="workflow/assemble/assemble.py",
        summary="Merges the formal proposals and the curated supplement values into 1_, "
                "then Concretizes and null-fills -> 4_.",
        inputs=[(OUT, "1_syntactic-semantics-api.json"),
                (CURATED, "formal-assignments.json"),
                (CURATED, "supplement")],
        outputs=[(OUT, "2_syntactic-semantics-formal-api.json"),
                 (OUT, "3_syntactic-semantics-formal-supplement-api.json"),
                 (OUT, "4_final-api.json")],
    ),
    Stage(
        name="validate",
        script="workflow/validate/consistency.py",
        args=["--report"],
        summary="Cross-entry consistency plus strict-schema conformance over the finished corpus. "
                "Reports; never drops an entry.",
        inputs=[(OUT, "1_syntactic-semantics-api.json"), (OUT, "4_final-api.json")],
        outputs=[(OUT, "validate-report.json")],
    ),
    Stage(
        name="provenance",
        script="workflow/provenance/report.py",
        summary="One record per value: which stage derived it, how, and whether a human "
                "has approved it.",
        inputs=[(OUT, "3_syntactic-semantics-formal-supplement-api.json"),
                (OUT, "4_final-api.json"),
                (CURATED, "field-provenance.json")],
        outputs=[(OUT, "provenance-report.json")],
    ),
    Stage(
        name="split",
        script="workflow/split/by_model.py",
        summary="Partitions the corpus and its provenance report into one shipped document "
                "per PPM.",
        inputs=[(OUT, "4_final-api.json")],
        outputs=[(OUT, "final-mpi-api.json")],
    ),
]

STAGE_NAMES = [s.name for s in STAGES]

# Duplicated from layout.ALL_MODELS, and checked against it in _apply_layout().
# The duplication is unavoidable rather than careless: argparse builds --ppm's
# help text before _apply_layout() runs, and layout cannot be imported any
# earlier because it resolves the three roots at import time, before this
# wrapper has had a chance to publish them.
ALL_MODELS = ["mpi", "shmem", "nccl", "nvshmem", "openmp", "cuda"]
# --regenerate token -> stage name. Only genuinely curated stages belong here.
CURATED_STAGES = {"formal": "assign"}

# Deleted by --prune-intermediates: the checkpoint files 4_final-api.json does
# not need to exist. The reports are not in here (they are the only record of
# what was flagged), nor are the derived staging schemas (regenerating them
# needs derive_schema.py, not a rebuild).
INTERMEDIATE_ARTIFACTS = [
    "0_syntactic-api.json",
    "1_syntactic-semantics-api.json",
    "2_syntactic-semantics-formal-api.json",
    "3_syntactic-semantics-formal-supplement-api.json",
]

EXTRA_SCRIPTS = {
    "check": "workflow/validate/consistency.py",
    "inspect_schema": "workflow/staging/derive_schema.py",
    "inspect_supplement": "workflow/supplement/propose.py",
}

TEST_SUITES = [
    "workflow/extract/test_emit.py",
    "workflow/classify/test_emit.py",
    "workflow/formal/test_shapes.py",
    "workflow/formal/test_grammar.py",
    "workflow/staging/test_staging_schema.py",
    "workflow/validate/test_curated.py",
    "workflow/split/test_by_model.py",
    "workflow/provenance/test_report.py",
]

layout = None  # set by _apply_layout() once the root options are known


def _apply_layout(args):
    """Publishes the chosen roots as environment variables and imports
    layout.py against them. Must happen before any path is resolved: layout
    resolves its roots at import time, and every stage subprocess inherits the
    same environment, so wrapper and stages can never disagree on a root."""
    global layout
    for value, var in ((args.external_inputs, "PPM_EXTERNAL_INPUTS_DIR"),
                       (args.curated_dir, "PPM_CURATED_DIR"),
                       (args.out, "PPM_OUT_DIR")):
        if value:
            os.environ[var] = os.path.abspath(os.path.expanduser(value))
    # Not a path, but it travels the same way and for the same reason: layout
    # resolves it at import time and every stage subprocess inherits it.
    if args.ppm:
        os.environ["PPM_MODELS"] = args.ppm
    import layout as _layout
    layout = _layout
    assert layout.ALL_MODELS == ALL_MODELS, (
        f"build.py and layout.py disagree on the model list: "
        f"{ALL_MODELS} vs {layout.ALL_MODELS}")


def _resolve(artifact):
    root, rel = artifact
    base = {OUT: layout.OUT_DIR, CURATED: layout.CURATED_DIR,
            EXTERNAL: layout.EXTERNAL_INPUTS_DIR}[root]
    return os.path.join(base, *rel.split("/"))


def _label(artifact):
    """Repo-relative when the root is inside the repo, absolute otherwise --
    so default builds read like the familiar paths and redirected ones are
    unambiguous."""
    path = _resolve(artifact)
    rel = os.path.relpath(path, _ROOT)
    return rel if not rel.startswith("..") else path


def _exists(artifact):
    return os.path.exists(_resolve(artifact))


def _describe(artifact):
    path = _resolve(artifact)
    if not os.path.exists(path):
        return "missing"
    st = os.stat(path)
    when = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
    return f"{st.st_size / 1024:.0f} KiB, {when}"


def _backup_dir():
    return os.path.join(layout.CURATED_DIR, "backups")


def _run_script(rel_script, args=(), dry_run=False, quiet=False):
    cmd = [sys.executable, os.path.join(_ROOT, rel_script), *args]
    shown = " ".join(["python3", rel_script, *args])
    if dry_run:
        print(f"  [dry-run] {shown}")
        return 0
    if not quiet:
        print(f"$ {shown}", flush=True)
    started = time.time()
    rc = subprocess.call(cmd, cwd=_ROOT,
                         stdout=subprocess.DEVNULL if quiet else None)
    if not quiet:
        print(f"  ({time.time() - started:.1f}s, exit {rc})")
    return rc


def _backup_curated(stage, quiet=False):
    """Copies a curated artifact aside before its stage overwrites it."""
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    for artifact in stage.outputs:
        src = _resolve(artifact)
        if not os.path.exists(src):
            continue
        os.makedirs(_backup_dir(), exist_ok=True)
        stem, ext = os.path.splitext(os.path.basename(src))
        dst = os.path.join(_backup_dir(), f"{stem}.{stamp}{ext}")
        shutil.copy2(src, dst)
        if not quiet:
            print(f"  backed up {_label(artifact)} -> {os.path.relpath(dst, _ROOT)}")


def _select_stages(args):
    if args.only:
        unknown = [n for n in args.only if n not in STAGE_NAMES]
        if unknown:
            raise SystemExit(f"unknown stage(s): {', '.join(unknown)} (known: {', '.join(STAGE_NAMES)})")
        selected = [s for s in STAGES if s.name in args.only]
    else:
        start = STAGE_NAMES.index(args.start) if args.start else 0
        stop = STAGE_NAMES.index(args.stop) if args.stop else len(STAGES) - 1
        if stop < start:
            raise SystemExit(f"--to {args.stop} comes before --from {args.start} in the chain")
        selected = STAGES[start:stop + 1]

    for name in args.skip:
        if name not in STAGE_NAMES:
            raise SystemExit(f"unknown stage in --skip: {name}")
    selected = [s for s in selected if s.name not in args.skip]

    regen = {CURATED_STAGES[k] for k in args.regenerate}
    final = []
    for s in selected:
        if not s.curated:
            final.append(s)
            continue
        asked_by_name = bool(args.only) and s.name in args.only
        if s.name in regen or asked_by_name:
            final.append(s)
        elif not all(_exists(o) for o in s.outputs):
            flag = [k for k, v in CURATED_STAGES.items() if v == s.name][0]
            if args.no_bootstrap:
                raise SystemExit(
                    f"curated artifact for stage '{s.name}' is missing "
                    f"({', '.join(_label(o) for o in s.outputs)}) and --no-bootstrap was given; "
                    f"run with --regenerate {flag} to create it")
            s.bootstrap = True
            final.append(s)

    for name in sorted(regen - {s.name for s in final}):
        flag = [k for k, v in CURATED_STAGES.items() if v == name][0]
        print(f"warning: --regenerate {flag} has no effect -- stage '{name}' is outside "
              f"this run's selection", file=sys.stderr)
    return final


def _preflight(selected):
    """Every input a selected stage needs must exist already or be produced by
    an earlier selected stage. Fails before running anything, so a long extract
    isn't wasted on a chain that can't finish."""
    will_produce = set()
    problems = []
    for s in selected:
        for artifact in s.inputs:
            if artifact in will_produce or _exists(artifact):
                continue
            producer = next((p.name for p in STAGES if artifact in p.outputs), None)
            hint = f" -- produced by stage '{producer}'" if producer else ""
            problems.append(f"stage '{s.name}' needs {_label(artifact)}, which is missing{hint}")
        will_produce.update(s.outputs)
    # The inputs this repository does not redistribute (workflow/fetch/). Extract
    # would not fail without them -- it globs the docs mirrors, and an empty glob
    # is just fewer descriptions -- so a missing one has to be caught here, or a
    # fresh clone would quietly build a thinner corpus than the shipped one.
    if any(s.name == "extract" for s in selected):
        sys.path.insert(0, os.path.join(_ROOT, "workflow", "fetch"))
        from fetch import missing_inputs
        for source_id, summary in missing_inputs(layout.MODELS).items():
            problems.append(f"stage 'extract' needs fetched input '{source_id}' ({summary}) -- "
                            f"run python3 workflow/fetch/fetch.py, or leave its model out with --ppm")
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        raise SystemExit(2)


def _print_plan(selected):
    for line in layout.describe():
        print(line)
    print("\nPlan:")
    for s in selected:
        tag = ""
        if s.curated:
            tag = " [CURATED, bootstrap]" if s.bootstrap else " [CURATED, regenerating]"
        print(f"  {s.name}{tag}")
        for o in s.outputs:
            print(f"      -> {_label(o)}")
    span = range(STAGE_NAMES.index(selected[0].name), STAGE_NAMES.index(selected[-1].name) + 1)
    consumed = {a for s in selected for a in s.inputs}
    for s in STAGES:
        if not s.curated or s in selected:
            continue
        if STAGE_NAMES.index(s.name) not in span and not (set(s.outputs) & consumed):
            continue
        flag = [k for k, v in CURATED_STAGES.items() if v == s.name][0]
        print(f"  {s.name} SKIPPED (curated) -- using {_label(s.outputs[0])} as-is "
              f"({_describe(s.outputs[0])}); --regenerate {flag} to rebuild")
    print()


def _cmd_list_stages():
    for line in layout.describe():
        print(line)
    print("\nWorkflow stages, in order:\n")
    for s in STAGES:
        mark = " [CURATED]" if s.curated else ""
        print(f"  {s.name}{mark}")
        print(f"      {s.summary}")
        print(f"      script:  {s.script}")
        for o in s.outputs:
            print(f"      output:  {_label(o):<52} ({_describe(o)})")
        print()
    print("A curated artifact is hand-correctable and is NOT rebuilt by a default")
    print("build -- see --regenerate.\n")
    print("Not part of the chain:")
    for flag, script in [("--check -- the validate stage without --report", EXTRA_SCRIPTS["check"]),
                         ("read-only, run by hand", EXTRA_SCRIPTS["inspect_schema"]),
                         ("read-only, run by hand", EXTRA_SCRIPTS["inspect_supplement"])]:
        print(f"  {script:<38} ({flag})")
    return 0


def _prune(dry_run, quiet):
    print("Pruning intermediate checkpoints:")
    for rel in INTERMEDIATE_ARTIFACTS:
        artifact = (OUT, rel)
        if not _exists(artifact):
            continue
        if dry_run:
            print(f"  [dry-run] rm {_label(artifact)}")
        else:
            os.remove(_resolve(artifact))
            if not quiet:
                print(f"  rm {_label(artifact)}")


_EPILOG = """\
examples:
  python3 workflow/build.py
      Default build: extract -> classify -> assemble, reusing
      curated/formal-assignments.json as-is. Writes instances/4_final-api.json.

  python3 workflow/build.py --to classify
      Stop after 1_syntactic-semantics-api.json (e.g. to inspect Heuristic
      Classification's output before anything merges on top of it).

  python3 workflow/build.py --from assemble
      Re-merge only. Use after editing curated/supplement/supplement-mpi.json
      or hand-correcting curated/formal-assignments.json -- nothing upstream
      is touched.

  python3 workflow/build.py --out /tmp/build-x
      Build into a scratch directory, leaving instances/ untouched. Missing
      output directories are created.

  python3 workflow/build.py --regenerate formal
      Rebuild curated/formal-assignments.json from assign.py, overwriting hand
      corrections (a timestamped copy lands in curated/backups/ first), then
      continue the normal build.

  python3 workflow/build.py --check
      Full build, then run the cross-entry consistency checker as a gate.

stage names for --from/--to/--only/--skip:
  """ + ", ".join(STAGE_NAMES) + """

see also:
  workflow/README.md                 what every script in workflow/ does
  curated/README.md                  what is curated, and why
  workflow/README.md the design each stage implements
"""


def build_parser():
    p = argparse.ArgumentParser(
        prog="workflow/build.py",
        description=(
            "Build 4_final-api.json by running the generation workflow's stages in order. "
            "Each stage is an independent script; this wrapper only sequences them, preflights "
            "their inputs, resolves the three directory roots, and protects the curated "
            "proposal file from being silently regenerated."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    roots = p.add_argument_group(
        "directory roots",
        "Passed to every stage as environment variables (resolved by "
        "workflow/common/layout.py), so the stages stay runnable standalone with the same "
        "defaults. Relative paths are resolved against the current directory.")
    roots.add_argument("--out", metavar="DIR",
                       help="where build output goes: the numbered checkpoints, the reports, "
                            "the supplement proposals and the derived staging schemas "
                            "(default: instances/; env PPM_OUT_DIR). Created if missing.")
    roots.add_argument("--curated-dir", metavar="DIR",
                       help="hand-authored/hand-corrected artifacts: curated/schemas/, supplement/, "
                            "review/, formal-assignments.json (default: curated/; "
                            "env PPM_CURATED_DIR)")
    roots.add_argument("--external-inputs", metavar="DIR",
                       help="third-party source material: standards, headers, docs mirrors "
                            "(default: external-inputs/; env PPM_EXTERNAL_INPUTS_DIR)")
    roots.add_argument("--ppm", metavar="MODEL[,MODEL...]",
                       help=f"cover only these programming models "
                            f"(default: all of {', '.join(ALL_MODELS)}; env PPM_MODELS). "
                            f"Only Extract reads the selection -- every later stage processes "
                            f"whatever is in the checkpoint it is handed -- so the chain and "
                            f"the curated artifacts are unaffected.")

    sel = p.add_argument_group(
        "stage selection",
        "Controls which stages run, and therefore which intermediate JSONs get written. "
        "Default: the full chain, minus curated stages.")
    sel.add_argument("--from", dest="start", metavar="STAGE", choices=STAGE_NAMES,
                     help="start at STAGE, assuming everything before it is already on disk")
    sel.add_argument("--to", dest="stop", metavar="STAGE", choices=STAGE_NAMES,
                     help="stop after STAGE (its outputs are the last written)")
    sel.add_argument("--only", metavar="STAGE[,STAGE...]", type=lambda v: v.split(","), default=[],
                     help="run exactly these stages, in chain order, and nothing else; "
                          "naming a curated stage here runs it")
    sel.add_argument("--skip", metavar="STAGE[,STAGE...]", type=lambda v: v.split(","), default=[],
                     help="drop these stages from whatever the selection would otherwise be")

    cur = p.add_argument_group(
        "curated artifacts",
        "curated/formal-assignments.json holds proposals a human corrects in place, with no "
        "upstream file for those corrections to live in instead. It is reused as-is unless you "
        "ask for it to be rebuilt.")
    cur.add_argument("--regenerate", metavar="WHICH", action="append", default=[],
                     help=f"rebuild a curated artifact: {' or '.join(sorted(CURATED_STAGES))} "
                          f"(or 'all'). Repeatable, or comma-separated. Overwrites hand "
                          f"corrections.")
    cur.add_argument("--no-backup", action="store_true",
                     help="don't copy the old curated file into curated/backups/ before "
                          "regenerating it")
    cur.add_argument("--no-bootstrap", action="store_true",
                     help="error out instead of auto-running a curated stage whose output "
                          "doesn't exist yet")

    conv = p.add_argument_group("extras (not part of the chain)")
    conv.add_argument("--check", action="store_true",
                      help="after the build, re-run the validate stage's script without "
                           "--report, which exits non-zero if it finds anything. The stage "
                           "itself only reports; this is the form to use in a gate.")
    conv.add_argument("--test", action="store_true",
                      help="before the build, run the six golden/unit test suites; abort if any fails")
    conv.add_argument("--prune-intermediates", action="store_true",
                      help="delete checkpoints 0_ through 3_ after a successful full build, "
                           "leaving only 4_final-api.json and the reports. Refused unless "
                           "'assemble' actually ran in this invocation.")

    out = p.add_argument_group("output")
    out.add_argument("-n", "--dry-run", action="store_true",
                     help="print the plan and the exact commands, run nothing")
    out.add_argument("-q", "--quiet", action="store_true",
                     help="suppress each stage's own stdout; keep this wrapper's summary")
    out.add_argument("--list-stages", action="store_true",
                     help="describe every stage with the current on-disk state of its outputs, then exit")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    _apply_layout(args)

    if args.list_stages:
        return _cmd_list_stages()

    regen = set()
    for chunk in args.regenerate:
        for token in (t.strip() for t in chunk.split(",")):
            if not token:
                continue
            if token == "all":
                regen.update(CURATED_STAGES)
            elif token in CURATED_STAGES:
                regen.add(token)
            else:
                raise SystemExit(
                    f"--regenerate takes {', '.join(sorted(CURATED_STAGES))} or 'all', got {token!r}")
    args.regenerate = regen

    if not args.dry_run:
        layout.ensure_out_dir()

    selected = _select_stages(args)
    if not selected:
        print("nothing to do -- the selection is empty")
        return 0

    _preflight(selected)
    _print_plan(selected)

    if args.test:
        for suite in TEST_SUITES:
            rc = _run_script(suite, dry_run=args.dry_run, quiet=args.quiet)
            if rc != 0:
                print(f"error: test suite failed: {suite}", file=sys.stderr)
                return rc

    started = time.time()
    for s in selected:
        if s.curated and not args.no_backup and not s.bootstrap:
            if args.dry_run:
                print(f"  [dry-run] back up {', '.join(_label(o) for o in s.outputs)} "
                      f"-> curated/backups/")
            else:
                _backup_curated(s, quiet=args.quiet)
        rc = _run_script(s.script, s.args, dry_run=args.dry_run, quiet=args.quiet)
        if rc != 0:
            print(f"error: stage '{s.name}' failed (exit {rc}); stopping", file=sys.stderr)
            return rc

    if args.prune_intermediates:
        if not any(s.name == "assemble" for s in selected):
            print("error: --prune-intermediates refused -- 'assemble' did not run in this "
                  "invocation, so 4_final-api.json may not reflect the files being deleted",
                  file=sys.stderr)
            return 2
        _prune(args.dry_run, args.quiet)

    if not args.dry_run:
        print(f"\nbuilt {', '.join(s.name for s in selected)} in {time.time() - started:.1f}s")
        shipped = [(OUT, f"final-{m}-api.json") for m in ALL_MODELS]
        shipped = [a for a in shipped if _exists(a)]
        if shipped:
            print("shipped artifacts:")
            for artifact in shipped:
                print(f"  {_label(artifact)} ({_describe(artifact)})")
            for name in ("provenance-report.json", "validate-report.json"):
                if _exists((OUT, name)):
                    print(f"  {_label((OUT, name))} ({_describe((OUT, name))})")
        else:
            final = (OUT, "4_final-api.json")
            if _exists(final):
                print(f"merged corpus: {_label(final)} ({_describe(final)})")

    rc = 0
    if args.check:
        rc = _run_script(EXTRA_SCRIPTS["check"], dry_run=args.dry_run, quiet=False)
        if rc != 0:
            print("consistency checker reported findings (see above) -- exit code reflects that, "
                  "the build itself succeeded")
    return rc


if __name__ == "__main__":
    sys.exit(main())
