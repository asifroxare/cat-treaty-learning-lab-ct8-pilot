"""Guarded local CT8 measurement of 25,000 full-detail occurrence rows."""
import argparse
import json
from pathlib import Path
import sys

from measure_pickle_gate import sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    try:
        print(json.dumps(sample(python, 10000, scenario="rows25k", max_seconds=90)), flush=True)
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as error:
        print(f"CT8 row-limit probe: STOPPED ({error})", file=sys.stderr)
        return 1
    print("CT8 row-limit probe: PASS (four-layer/hours maxima still open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
