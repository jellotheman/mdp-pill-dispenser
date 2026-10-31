"""Run scenarios against the actual shared C++ controller. No Arduino board required."""
import subprocess
import sys

from native_build import ROOT, build


def main():
    binary = build()
    arguments = [str(binary)] + (["--events"] if "--events" in sys.argv else [])
    result = subprocess.run(arguments, check=True, text=True, capture_output=True)
    print(result.stdout, end="")
    events = [line[6:] for line in result.stdout.splitlines() if line.startswith("EVENT ")]
    if events:
        output = ROOT / "output"
        output.mkdir(exist_ok=True)
        (output / "demo-events.jsonl").write_text("\n".join(events) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
