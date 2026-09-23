"""
The three roots every workflow script reads and writes, resolved in one place.

    external-inputs/   third-party source material (vendored standards, headers,
                       docs mirrors). Read-only to this workflow.
    curated/           hand-authored or hand-corrected artifacts: the schema
                       family, the shape catalog, the per-PPM supplement inputs,
                       the formal-assignment proposals, and the review records.
                       Changes rarely, deliberately, and never as a side effect
                       of a build.
    instances/         everything a build produces. Safe to delete and
                       regenerate.

Each root can be redirected with an environment variable, which is how
workflow/build.py's --external-inputs / --curated-dir / --out are plumbed
through to the stage scripts. Setting one by hand does the same thing:

    PPM_OUT_DIR=/tmp/build-x python3 workflow/extract/cli.py

Why env vars rather than a --out flag on every stage: the stage scripts are
deliberately argument-free, single-purpose drivers, and each reads several
inputs from more than one root -- giving each of them its own path flags would
multiply the surface with no gain, since a build always wants the same three
roots for every stage. Unset variables give the repo-relative defaults above,
so every script keeps working standalone with no environment at all.

Relative values are resolved against the current working directory, then
normalized to absolute, so a caller can pass ../shared-curated without
depending on which directory a stage script happens to be run from.

One more variable travels the same way for the same reason: PPM_MODELS selects
which programming models a build covers (build.py --ppm). Only Extract reads it
-- every later stage processes whatever families are in the checkpoint it is
handed -- but it is resolved here so that "which models is this build about" has
one answer that the wrapper and the stages cannot disagree on.
"""

import os

# .../<repo>/workflow/common/layout.py -> <repo>
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENV_VARS = {
    "external_inputs": "PPM_EXTERNAL_INPUTS_DIR",
    "curated": "PPM_CURATED_DIR",
    "out": "PPM_OUT_DIR",
    "models": "PPM_MODELS",
}


def _resolve(env_var, default_name):
    value = os.environ.get(env_var)
    if not value:
        return os.path.join(ROOT, default_name)
    return os.path.abspath(os.path.expanduser(value))


EXTERNAL_INPUTS_DIR = _resolve(ENV_VARS["external_inputs"], "external-inputs")
CURATED_DIR = _resolve(ENV_VARS["curated"], "curated")
OUT_DIR = _resolve(ENV_VARS["out"], "instances")

# The models this workflow has an Extract adapter for, in the order Extract runs
# them -- the schema's whole identity.model enum since openmp and cuda gained
# adapters (2026-09-11).
ALL_MODELS = ["mpi", "shmem", "nccl", "nvshmem", "openmp", "cuda"]


def _resolve_models():
    value = os.environ.get(ENV_VARS["models"])
    if not value:
        return list(ALL_MODELS)
    requested = [m.strip().lower() for m in value.split(",") if m.strip()]
    unknown = [m for m in requested if m not in ALL_MODELS]
    if unknown:
        raise SystemExit(
            f"{ENV_VARS['models']}: unknown model(s) {', '.join(unknown)}. "
            f"Known: {', '.join(ALL_MODELS)}")
    if not requested:
        raise SystemExit(f"{ENV_VARS['models']} is set but names no model.")
    # Deduplicated, and back into ALL_MODELS order rather than the order the
    # caller happened to type: Extract's output is sorted by key anyway, so
    # honouring the caller's order would only make two equivalent invocations
    # look different in the run log.
    return [m for m in ALL_MODELS if m in set(requested)]


MODELS = _resolve_models()

# Sub-roots. Deliberately not independently overridable: they are structure
# within a root, not roots of their own, and letting them drift apart would
# make "which curated set is this build using" unanswerable from one variable.
SCHEMAS_DIR = os.path.join(CURATED_DIR, "schemas")      # JSON Schemas only
SHAPES_DIR = os.path.join(CURATED_DIR, "shapes")        # the shape catalog + its authored bindings
SUPPLEMENT_DIR = os.path.join(CURATED_DIR, "supplement")
REVIEW_DIR = os.path.join(CURATED_DIR, "review")

# Config, not schema: the field -> (tier, stage) table the schema machinery
# reads. Lives at the curated root because it governs the schemas rather than
# being one of them.
FIELD_PROVENANCE_PATH = os.path.join(CURATED_DIR, "field-provenance.json")


def external_input(*parts):
    return os.path.join(EXTERNAL_INPUTS_DIR, *parts)


def curated(*parts):
    return os.path.join(CURATED_DIR, *parts)


def schema(*parts):
    return os.path.join(SCHEMAS_DIR, *parts)


def shapes(*parts):
    return os.path.join(SHAPES_DIR, *parts)


def out(*parts):
    return os.path.join(OUT_DIR, *parts)


def ensure_out_dir(*parts):
    """Creates the output directory (and any sub-path given) and returns it.
    Every writer calls this rather than assuming instances/ exists, so a build
    redirected with --out to a fresh path works with no setup."""
    path = os.path.join(OUT_DIR, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def describe():
    """One line per root, for a build's own banner."""
    return [
        f"external-inputs: {EXTERNAL_INPUTS_DIR}",
        f"curated:         {CURATED_DIR}",
        f"out:             {OUT_DIR}",
        f"models:          {', '.join(MODELS)}",
    ]
