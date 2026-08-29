"""Sample a fresh review batch from production traces and push it to
the viewer.

Usage: uv run python tests/evals/sample_batch.py [--size 20] [--seed S]
       [--dir PATH] [--host URL] [--no-post]

The addon writes one trace per curation session to
traces/<stamp>/note_<seed_id>.trialN.json. This tool picks the next
slice of sessions worth reviewing:

1. Exclude records whose file name or note_id already has an
   annotation anywhere (annotations.json next to the traces).
2. Keep one run per note_id — the most informative one (proposes
   changes over none, then more changes, then more steps).
3. Round-robin across outcome statuses (applied / rejected /
   no_changes / cancelled / failed) so every batch mixes session
   kinds, and order within an outcome by note_id so the batch
   spreads across the collection. --seed shuffles within outcomes.

The result is written to batch.json in the trace directory (the
viewer reads it) and POSTed to the viewer's /api/batch endpoint,
which replaces any previous batch. Reasons are generated from each
record's facts; refine them by hand if a choice needs explaining.
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

TRACES = Path(__file__).resolve().parent.parent.parent / "traces"
DEFAULT_HOST = "http://localhost:5000"


def load_trace_files(traces_dir: Path) -> list[tuple[str, dict]]:
    """All trace records as (run_stamp, record) pairs, stamps sorted."""
    found = []
    for stamp in sorted(p.name for p in traces_dir.iterdir() if p.is_dir()):
        pattern = str(traces_dir / stamp / "*.trial*.json")
        for path in sorted(glob.glob(pattern)):
            with open(path, encoding="utf-8") as fh:
                found.append((stamp, json.load(fh)))
    return found


def load_annotated(traces_dir: Path) -> tuple[set[str], set[str]]:
    """(file names, note_ids) that already carry an annotation.

    Annotations live in each run's annotations.json, keyed by record
    file name, so a note reviewed once in any run is never
    re-suggested.
    """
    names: set[str] = set()
    note_ids: set[str] = set()
    for ann_file in sorted(traces_dir.glob("*/annotations.json")):
        for key in json.loads(ann_file.read_text(encoding="utf-8")):
            names.add(key)
            note_ids.add(key.split(".")[0])
    return names, note_ids


def _informativeness(record: dict) -> tuple:
    """Rank runs of the same note: changes beat steps beat staleness."""
    changes = record.get("change_set", [])
    return (
        len(changes) > 0,  # runs that proposed something rank first
        len(changes),  # more proposals first
        len(record.get("transcript", [])),  # then deeper sessions
    )


def select_batch(
    traces_dir: Path, size: int, seed: int | None = None
) -> list[dict]:
    """One fresh, outcome-diverse batch entry per note_id.

    Returns [{run, task_id, trial, reason}] limited to `size`, ready
    for batch.json or POST /api/batch. Deterministic unless seed is
    given. Records with an existing annotation (by file name or
    note_id) are never re-suggested.
    """
    records = load_trace_files(traces_dir)
    names, note_ids = load_annotated(traces_dir)

    raw = [
        (stamp, r)
        for stamp, r in records
        if r["task_id"] not in note_ids
        and f"{r['task_id']}.trial{r.get('trial', 0)}.json" not in names
    ]
    if not raw:
        return []

    # Fresh batch never repeats a note: one informative run per id.
    best: dict[str, tuple[str, dict]] = {}
    for stamp, r in raw:
        rid = r["task_id"]
        if rid not in best or _informativeness(r) > _informativeness(
            best[rid][1]
        ):
            best[rid] = (stamp, r)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for stamp, r in best.values():
        buckets[r.get("outcome", {}).get("status", "unknown")].append(
            {
                "run": stamp,
                "task_id": r["task_id"],
                "trial": 0,
                "reason": reason_for(r),
            }
        )
    for entries in buckets.values():
        entries.sort(key=lambda e: e["task_id"])
        if seed is not None:
            random.Random(seed).shuffle(entries)

    # Round-robin: one from each outcome bucket before revisiting any,
    # so a small batch still mixes session kinds.
    batch: list[dict] = []
    while buckets and len(batch) < size:
        for status in list(buckets):
            entries = buckets[status]
            if entries:
                batch.append(entries.pop(0))
            if not entries:
                del buckets[status]
            if len(batch) == size:
                break
    return batch


def reason_for(record: dict) -> str:
    """One-line factual why-this-session for the batch card."""
    changes = record.get("change_set", [])
    kinds = ", ".join(sorted({c.get("type", "?") for c in changes}))
    parts = [f"{record.get('outcome', {}).get('status', '?')}"]
    if changes:
        parts.append(f"{len(changes)} {kinds} proposal(s)")
    parts.append(f"{len(record.get('transcript', []))} steps")
    return "; ".join(parts)


def push_batch(batch: list[dict], host: str, out_path: Path) -> None:
    """Persist batch.json next to the traces and POST it to the viewer."""
    out_path.write_text(
        json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if not batch:
        return
    req = urllib.request.Request(
        f"{host}/api/batch",
        data=json.dumps({"batch": batch}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--size", type=int, default=20)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--dir", type=Path, default=TRACES)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--no-post", action="store_true")
    args = ap.parse_args()

    batch = select_batch(args.dir, args.size, args.seed)
    if not batch:
        print(
            "No un-annotated records left — nothing to batch.",
            file=sys.stderr,
        )
        sys.exit(1)

    out_path = args.dir / "batch.json"
    if not args.no_post:
        try:
            push_batch(batch, args.host, out_path)
            print(f"Pushed {len(batch)} sessions to {args.host}/api/batch")
        except (urllib.error.URLError, OSError) as err:
            print(
                f"POST failed ({err}); wrote batch.json only.",
                file=sys.stderr,
            )
            out_path.write_text(
                json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    else:
        out_path.write_text(
            json.dumps(batch, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {out_path} ({len(batch)} sessions).")

    for entry in batch:
        print(f"  {entry['run']}  {entry['task_id']:24s} {entry['reason']}")


if __name__ == "__main__":
    main()
