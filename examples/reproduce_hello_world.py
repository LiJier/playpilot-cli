"""Reproduce the recorded CLI run against a pinned public test APK.

Downloads only with --download; the APK is parsed, never installed or executed.
"""

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download the pinned public APK if missing")
    parser.add_argument("--check", action="store_true", help="Compare with the recorded stdout without overwriting it")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "examples/hello-world-source.json").read_text(encoding="utf-8"))
    package = ROOT / metadata["local_path"]
    if not package.exists():
        if not args.download:
            parser.error("Sample missing. Use --download to fetch the public test APK.")
        with urllib.request.urlopen(metadata["url"], timeout=45) as response:
            data = response.read(5_000_001)
        if hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise SystemExit("Downloaded sample checksum differs; no file was written.")
        package.parent.mkdir(parents=True, exist_ok=True)
        package.write_bytes(data)
    if hashlib.sha256(package.read_bytes()).hexdigest() != metadata["sha256"]:
        raise SystemExit("Local sample checksum differs; refusing to inspect it.")
    run = subprocess.run(
        [sys.executable, "-X", "utf8", "cli.py", metadata["local_path"], "--lang", "en"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if run.returncode:
        sys.stderr.write(run.stderr)
        raise SystemExit(run.returncode)
    output = "\n".join(line.rstrip() for line in run.stdout.splitlines()).rstrip() + "\n"
    destination = ROOT / "examples/hello-world-cli.txt"
    if args.check:
        expected = destination.read_text(encoding="utf-8")
        if expected != output:
            sys.stdout.writelines(difflib.unified_diff(expected.splitlines(True), output.splitlines(True), fromfile="recorded", tofile="current"))
            raise SystemExit(1)
        print("Recorded CLI stdout reproduced exactly.")
    else:
        destination.write_text(output, encoding="utf-8")
        print("Updated examples/hello-world-cli.txt; review changes before committing.")


if __name__ == "__main__":
    main()
