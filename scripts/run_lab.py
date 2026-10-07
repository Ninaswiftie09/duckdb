import subprocess
import sys

from common import ROOT


def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, check=True)


def main():
    run("download_data.py", "--years", "2026")
    run("analyze.py", "--years", "2026")
    run("download_data.py", "--years", "2024", "2026")
    run("analyze.py", "--years", "2024", "2026")
    run("benchmark.py", "--years", "2024", "2026", "--repeats", "3")
    run("download_data.py", "--years", "2024", "2025", "2026")
    run("analyze.py", "--years", "2024", "2025", "2026")
    run("build_dashboard.py")
    run("write_report.py")


if __name__ == "__main__":
    main()
