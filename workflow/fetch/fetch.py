#!/usr/bin/env python3
"""
Fetch the third-party inputs this repository does not redistribute.

Most of external-inputs/ is vendored, because its licences allow it. Four
sources are not, and a fresh clone has to fetch them before a full build:

    cuda-headers   CUDA 13.1 runtime headers   NVIDIA proprietary
    cuda-docs      CUDA 13.1 behavioural pages docs.nvidia.com, no licence
    nccl-docs      NCCL 2.30 documentation     docs.nvidia.com, no licence
    nvshmem-docs   NVSHMEM 3.7.0 documentation docs.nvidia.com, no licence

For the NVSHMEM pages the pinned checksums are those of NVIDIA's version
archive, which re-renders 3.7.0 in a newer theme than the live-site copy the
corpus was first built from; Extract reads identical values from both
(manifest.json's link_base_note).

## Transparent by construction

Everything this script downloads and writes is listed in manifest.json beside
it: one URL per download, one destination per file, and the sha256 each file
must have. The script reads nothing else and has no other network access, so
reading the manifest is reading everything it can do. --dry-run prints the
same list without touching the network.

Every file is checked against its pinned sha256 before anything is installed.
A source is installed all-or-nothing: one mismatch and none of its files are
written, so external-inputs/ only ever holds the pinned bytes. The checksums
pin exact files, not whatever a URL serves today.

The docs are fetched as raw HTML and converted to Markdown locally with
workflow/ingestion/html_to_markdown.py, the same converter that produced the
original mirror. The Markdown is checked too, so a converter change that would
alter what Extract reads shows up here rather than as a silently different
corpus.

## When a source cannot be downloaded

Every URL points at a versioned archive rather than a live site, so a source
should stay downloadable. If one disappears, its manifest entry gets an
"unavailable" field saying why, and fetch.py reports it instead of trying.
--from-dir DIR installs from an existing copy instead, laid out like
external-inputs/ (for example another checkout). The same checksums decide
what is accepted, so a copy is only as good as its bytes.

    python3 workflow/fetch/fetch.py                        # everything
    python3 workflow/fetch/fetch.py --ppm nccl,cuda        # some models
    python3 workflow/fetch/fetch.py --dry-run              # show, don't fetch
    python3 workflow/fetch/fetch.py --check                # verify what is on disk
    python3 workflow/fetch/fetch.py --from-dir ../old/external-inputs

workflow/build.py calls missing_inputs() before Extract, so a build without
these files stops with a pointer here instead of producing a thinner corpus.
"""

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "common"))
sys.path.insert(0, os.path.join(_HERE, "..", "ingestion"))
import layout  # noqa: E402
from html_to_markdown import convert_tree  # noqa: E402

MANIFEST_PATH = os.path.join(_HERE, "manifest.json")
USER_AGENT = "USIS-fetch/1 (+https://github.com/RWTH-HPC/USIS)"


def load_manifest(path=MANIFEST_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["sources"]


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def expected_files(source):
    """[(path relative to the source's dest, sha256), ...] -- every file the
    source installs. For docs that is the raw HTML and the Markdown from it."""
    if source["kind"] == "archive":
        return [(f["path"], f["sha256"]) for f in source["files"]]
    files = []
    for page in source["pages"]:
        md = page["path"][:-len(".html")] + ".md"
        files.append((os.path.join(source["raw_dir"], page["path"]), page["sha256"]))
        files.append((os.path.normpath(os.path.join(source["md_dir"], md)), page["md_sha256"]))
    return files


def verify(source, root):
    """-> [(relpath, problem), ...] for the source's files under root; empty
    when every file is present with its pinned checksum."""
    problems = []
    for rel, sha in expected_files(source):
        path = os.path.join(root, source["dest"], rel)
        if not os.path.exists(path):
            problems.append((rel, "missing"))
        elif _sha256(Path(path).read_bytes()) != sha:
            problems.append((rel, "checksum differs"))
    return problems


def missing_inputs(models, root=None):
    """-> {source id: problem summary} for every source a model in `models`
    needs that is not fully present and verified. For build.py's preflight."""
    root = root or layout.EXTERNAL_INPUTS_DIR
    out = {}
    for source in load_manifest():
        if source["model"] not in models:
            continue
        problems = verify(source, root)
        if problems:
            n_missing = sum(1 for _, p in problems if p == "missing")
            out[source["id"]] = (f"{n_missing} missing, {len(problems) - n_missing} "
                                 f"with a different checksum, of {len(expected_files(source))} files")
    return out


def _download(url, attempts=3):
    print(f"    GET {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except OSError as e:
            if attempt == attempts:
                raise RuntimeError(f"{url}: {e}") from e
            time.sleep(2 * attempt)


def _stage_archive(source, from_dir):
    """-> {relpath: bytes} for an archive source, or raises RuntimeError."""
    if from_dir:
        return {f["path"]: _read_local(from_dir, source, f["path"]) for f in source["files"]}
    data = _download(source["url"])
    if _sha256(data) != source["sha256"]:
        raise RuntimeError(f"archive checksum differs: {source['url']}")
    staged = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tar:
        for f in source["files"]:
            member = tar.extractfile(f["member"])
            if member is None:
                raise RuntimeError(f"{f['member']} is not a file in the archive")
            staged[f["path"]] = member.read()
    return staged


def _stage_pages(source, from_dir):
    """-> {relpath: bytes} for a docs source: the raw pages, downloaded (or
    copied) as listed, plus the Markdown converted from them locally."""
    staged = {}
    with tempfile.TemporaryDirectory() as tmp:
        raw_dir = Path(tmp, "raw")
        for page in source["pages"]:
            rel = os.path.join(source["raw_dir"], page["path"])
            data = (_read_local(from_dir, source, rel) if from_dir
                    else _download(source["fetch_base"] + page["path"]))
            staged[rel] = data
            target = raw_dir / page["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        print(f"    convert: html_to_markdown.py <raw> <md> {source['link_base']}")
        md_dir = Path(tmp, "md")
        for md_path in convert_tree(raw_dir, md_dir, source["link_base"]):
            rel = os.path.normpath(os.path.join(source["md_dir"], md_path.relative_to(md_dir)))
            staged[rel] = md_path.read_bytes()
    return staged


def _read_local(from_dir, source, rel):
    path = os.path.join(from_dir, source["dest"], rel)
    print(f"    copy {path}")
    try:
        return Path(path).read_bytes()
    except OSError as e:
        raise RuntimeError(f"{path}: {e.strerror}") from e


def fetch(source, root, from_dir=None, force=False):
    """Stages, verifies and installs one source. -> True when it ends up
    present and verified."""
    dest = os.path.join(root, source["dest"])
    problems = verify(source, root)
    if not problems:
        print(f"  {source['id']}: present and verified, nothing to do")
        return True
    if not force and any(p != "missing" for _, p in problems):
        print(f"  {source['id']}: refused -- files already in {dest} have a different checksum "
              f"(e.g. {next(r for r, p in problems if p != 'missing')}); "
              f"--force replaces them with the pinned version")
        return False
    if source.get("unavailable") and not from_dir:
        print(f"  {source['id']}: unavailable for download.\n    {source['unavailable']}")
        return False

    print(f"  {source['id']}: -> {dest}")
    try:
        staged = (_stage_archive if source["kind"] == "archive" else _stage_pages)(source, from_dir)
    except RuntimeError as e:
        print(f"  {source['id']}: failed, nothing installed -- {e}")
        return False

    expected = dict(expected_files(source))
    bad = [rel for rel, sha in expected.items() if rel not in staged or _sha256(staged[rel]) != sha]
    if bad:
        print(f"  {source['id']}: {len(bad)} of {len(expected)} files do not match the manifest; "
              f"nothing installed:")
        for rel in bad[:10]:
            print(f"    {rel}")
        if len(bad) > 10:
            print(f"    ... and {len(bad) - 10} more")
        return False

    for rel in expected:
        path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(staged[rel])
    print(f"  {source['id']}: installed {len(expected)} files, all verified")
    return True


def _print_plan(source, root, from_dir):
    print(f"  {source['id']} ({source['model']}): {source['why_not_vendored']}")
    print(f"    into {os.path.join(root, source['dest'])}")
    if source.get("unavailable") and not from_dir:
        print(f"    UNAVAILABLE: {source['unavailable']}")
    elif from_dir:
        print(f"    copy from {os.path.join(from_dir, source['dest'])}")
    elif source["kind"] == "archive":
        print(f"    GET {source['url']}")
        for f in source["files"]:
            print(f"      extract {f['member']} -> {f['path']}")
    else:
        for page in source["pages"]:
            print(f"    GET {source['fetch_base']}{page['path']}")
        print(f"    then convert {len(source['pages'])} pages to Markdown locally")


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Fetch the third-party inputs listed in workflow/fetch/manifest.json "
                    "and verify them against their pinned sha256.")
    p.add_argument("--ppm", metavar="MODEL[,MODEL...]",
                   help="only sources for these models (default: every model with one)")
    p.add_argument("--from-dir", metavar="DIR",
                   help="copy from DIR, laid out like external-inputs/, instead of downloading")
    p.add_argument("--dry-run", action="store_true", help="print what would be fetched and stop")
    p.add_argument("--check", action="store_true",
                   help="only verify what is on disk; no network, exit 1 if anything is missing")
    p.add_argument("--force", action="store_true",
                   help="replace files on disk whose checksum differs from the manifest")
    args = p.parse_args(argv)

    root = layout.EXTERNAL_INPUTS_DIR
    sources = load_manifest()
    if args.ppm:
        models = {m.strip().lower() for m in args.ppm.split(",") if m.strip()}
        unknown = models - set(layout.ALL_MODELS)
        if unknown:
            p.error(f"unknown model(s) {', '.join(sorted(unknown))}")
        sources = [s for s in sources if s["model"] in models]
    from_dir = os.path.abspath(args.from_dir) if args.from_dir else None

    if args.dry_run:
        print("Would fetch (manifest: workflow/fetch/manifest.json):")
        for s in sources:
            _print_plan(s, root, from_dir)
        return 0

    if args.check:
        failing = 0
        for s in sources:
            problems = verify(s, root)
            print(f"  {s['id']}: " + ("ok" if not problems else
                  f"{len(problems)} of {len(expected_files(s))} files missing or different"))
            failing += bool(problems)
        return 1 if failing else 0

    ok = [fetch(s, root, from_dir=from_dir, force=args.force) for s in sources]
    failed = [s["id"] for s, good in zip(sources, ok) if not good]
    if failed:
        print(f"\nnot installed: {', '.join(failed)}. A build for their models will refuse to "
              f"run; build the others with --ppm.")
        return 1
    print("\nall selected inputs present and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
