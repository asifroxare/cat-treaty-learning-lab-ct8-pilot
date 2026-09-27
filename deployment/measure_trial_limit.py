"""Guarded local measurement of CT6's exact 10,000-trial limit."""
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
        print(json.dumps(sample(python, 10000)), flush=True)
    except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as error:
        print(f"CT8 trial-limit probe: STOPPED ({error})", file=sys.stderr)
        return 1
    print("CT8 trial-limit probe: PASS (occurrence/layer maxima still open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
